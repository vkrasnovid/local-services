"use client";

import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { Booking, PaginatedResponse } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/pagination";
import { Eye } from "lucide-react";
import { formatCurrency, formatDate } from "@/lib/utils";
import { toast } from "sonner";

const PAGE_SIZE = 20;

const STATUS_OPTIONS = [
  { value: "all", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "confirmed", label: "Confirmed" },
  { value: "in_progress", label: "In Progress" },
  { value: "completed", label: "Completed" },
  { value: "cancelled", label: "Cancelled" },
] as const;

const STATUS_BADGE_VARIANT: Record<
  Booking["status"],
  "warning" | "info" | "success" | "destructive"
> = {
  pending: "warning",
  confirmed: "info",
  in_progress: "info",
  completed: "success",
  cancelled: "destructive",
};

const STATUS_LABEL: Record<Booking["status"], string> = {
  pending: "Pending",
  confirmed: "Confirmed",
  in_progress: "In Progress",
  completed: "Completed",
  cancelled: "Cancelled",
};

function truncateId(id: string): string {
  if (id.length <= 8) return id;
  return id.slice(0, 8) + "...";
}

export default function BookingsPage() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const fetchBookings = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: PAGE_SIZE,
      };
      if (statusFilter !== "all") {
        params.status = statusFilter;
      }
      if (dateFrom) {
        params.date_from = dateFrom;
      }
      if (dateTo) {
        params.date_to = dateTo;
      }
      const { data } = await api.get<PaginatedResponse<Booking>>(
        "/admin/bookings",
        { params }
      );
      setBookings(data.items);
      setTotalPages(data.pages);
      setTotal(data.total);
    } catch {
      toast.error("Failed to load bookings");
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, dateFrom, dateTo]);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  function handleStatusChange(value: string) {
    setStatusFilter(value);
    setPage(1);
  }

  function handleDateFromChange(e: React.ChangeEvent<HTMLInputElement>) {
    setDateFrom(e.target.value);
    setPage(1);
  }

  function handleDateToChange(e: React.ChangeEvent<HTMLInputElement>) {
    setDateTo(e.target.value);
    setPage(1);
  }

  function handleViewBooking(booking: Booking) {
    setSelectedBooking(booking);
    setDetailOpen(true);
  }

  function handleCloseDetail() {
    setDetailOpen(false);
    setSelectedBooking(null);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Bookings</h1>
        <p className="text-muted-foreground">
          Manage and view all bookings on the platform
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            <div className="w-[200px]">
              <label className="mb-1 block text-sm font-medium">Status</label>
              <Select value={statusFilter} onValueChange={handleStatusChange}>
                <SelectTrigger>
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="w-[180px]">
              <label className="mb-1 block text-sm font-medium">
                Date From
              </label>
              <Input
                type="date"
                value={dateFrom}
                onChange={handleDateFromChange}
              />
            </div>
            <div className="w-[180px]">
              <label className="mb-1 block text-sm font-medium">Date To</label>
              <Input
                type="date"
                value={dateTo}
                onChange={handleDateToChange}
              />
            </div>
            <Button
              variant="outline"
              onClick={() => {
                setStatusFilter("all");
                setDateFrom("");
                setDateTo("");
                setPage(1);
              }}
            >
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Bookings {!loading && `(${total})`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : bookings.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              No bookings found
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead>Master</TableHead>
                    <TableHead>Service</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {bookings.map((booking) => (
                    <TableRow key={booking.id}>
                      <TableCell
                        className="font-mono text-sm"
                        title={booking.id}
                      >
                        {truncateId(booking.id)}
                      </TableCell>
                      <TableCell>
                        {booking.client.first_name} {booking.client.last_name}
                      </TableCell>
                      <TableCell>
                        {booking.master.user.first_name}{" "}
                        {booking.master.user.last_name}
                      </TableCell>
                      <TableCell>{booking.service.name}</TableCell>
                      <TableCell>
                        {booking.slot
                          ? `${formatDate(booking.slot.date)} ${booking.slot.start_time}`
                          : formatDate(booking.created_at)}
                      </TableCell>
                      <TableCell>
                        <Badge variant={STATUS_BADGE_VARIANT[booking.status]}>
                          {STATUS_LABEL[booking.status]}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(booking.price)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleViewBooking(booking)}
                          title="View details"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <Pagination
                page={page}
                totalPages={totalPages}
                onPageChange={setPage}
              />
            </>
          )}
        </CardContent>
      </Card>

      <Dialog open={detailOpen} onOpenChange={handleCloseDetail}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Booking Details</DialogTitle>
            <DialogDescription>
              Full information about the selected booking
            </DialogDescription>
          </DialogHeader>
          {selectedBooking && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Booking ID
                  </p>
                  <p className="font-mono text-sm">{selectedBooking.id}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Status
                  </p>
                  <Badge
                    variant={STATUS_BADGE_VARIANT[selectedBooking.status]}
                  >
                    {STATUS_LABEL[selectedBooking.status]}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Client
                  </p>
                  <p>
                    {selectedBooking.client.first_name}{" "}
                    {selectedBooking.client.last_name}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Master
                  </p>
                  <p>
                    {selectedBooking.master.user.first_name}{" "}
                    {selectedBooking.master.user.last_name}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Service
                  </p>
                  <p>{selectedBooking.service.name}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Amount
                  </p>
                  <p className="font-semibold">
                    {formatCurrency(selectedBooking.price)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Date / Time
                  </p>
                  <p>
                    {selectedBooking.slot
                      ? `${formatDate(selectedBooking.slot.date)} ${selectedBooking.slot.start_time}`
                      : formatDate(selectedBooking.created_at)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Address
                  </p>
                  <p>{selectedBooking.address || "Not specified"}</p>
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Created At
                </p>
                <p>{formatDate(selectedBooking.created_at)}</p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
