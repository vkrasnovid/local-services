"use client";

import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { MasterVerification, PaginatedResponse } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/pagination";
import { Check, X, Eye } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";

const statusBadgeVariant: Record<string, "warning" | "success" | "destructive"> = {
  pending: "warning",
  verified: "success",
  rejected: "destructive",
};

export default function MastersPage() {
  const [tab, setTab] = useState("pending");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedResponse<MasterVerification> | null>(null);
  const [loading, setLoading] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [selectedMaster, setSelectedMaster] = useState<MasterVerification | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const statusParam = tab === "all" ? "" : tab;
      const params: Record<string, string | number> = { page, page_size: 20 };
      if (statusParam) {
        params.status = statusParam;
      }
      const response = await api.get<PaginatedResponse<MasterVerification>>(
        "/admin/verifications",
        { params }
      );
      setData(response.data);
    } catch {
      toast.error("Failed to load verifications");
    } finally {
      setLoading(false);
    }
  }, [tab, page]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleTabChange = (value: string) => {
    setTab(value);
    setPage(1);
  };

  const handleApprove = async (masterId: string) => {
    try {
      await api.patch(`/admin/verifications/${masterId}`, { status: "verified" });
      toast.success("Master approved successfully");
      fetchData();
    } catch {
      toast.error("Failed to approve master");
    }
  };

  const handleRejectClick = (master: MasterVerification) => {
    setSelectedMaster(master);
    setRejectReason("");
    setRejectDialogOpen(true);
  };

  const handleRejectConfirm = async () => {
    if (!selectedMaster) return;
    try {
      await api.patch(`/admin/verifications/${selectedMaster.master_id}`, {
        status: "rejected",
        reason: rejectReason,
      });
      toast.success("Master rejected");
      setRejectDialogOpen(false);
      setSelectedMaster(null);
      setRejectReason("");
      fetchData();
    } catch {
      toast.error("Failed to reject master");
    }
  };

  const handleView = (master: MasterVerification) => {
    setSelectedMaster(master);
    setViewDialogOpen(true);
  };

  const renderTable = (items: MasterVerification[]) => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Category</TableHead>
          <TableHead>Phone</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Documents</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.length === 0 ? (
          <TableRow>
            <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
              No verifications found
            </TableCell>
          </TableRow>
        ) : (
          items.map((master) => (
            <TableRow key={master.master_id}>
              <TableCell className="font-medium">
                {master.user.first_name} {master.user.last_name}
              </TableCell>
              <TableCell>{master.category}</TableCell>
              <TableCell>{master.user.phone}</TableCell>
              <TableCell>
                <Badge variant={statusBadgeVariant[master.verification_status]}>
                  {master.verification_status}
                </Badge>
              </TableCell>
              <TableCell>{master.verification_docs.length}</TableCell>
              <TableCell>{formatDate(master.created_at)}</TableCell>
              <TableCell>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleView(master)}
                    title="View details"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  {master.verification_status === "pending" && (
                    <>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleApprove(master.master_id)}
                        title="Approve"
                        className="text-green-600 hover:text-green-700"
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRejectClick(master)}
                        title="Reject"
                        className="text-red-600 hover:text-red-700"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );

  const tabContent = (
    <>
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      ) : (
        <>
          {renderTable(data?.items ?? [])}
          {data && (
            <Pagination
              page={data.page}
              totalPages={data.pages}
              onPageChange={setPage}
            />
          )}
        </>
      )}
    </>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Masters</h1>
        <p className="text-muted-foreground">
          Manage master verifications and approvals
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Verifications</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={tab} onValueChange={handleTabChange}>
            <TabsList>
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="pending">Pending</TabsTrigger>
              <TabsTrigger value="verified">Verified</TabsTrigger>
              <TabsTrigger value="rejected">Rejected</TabsTrigger>
            </TabsList>
            <TabsContent value={tab} className="mt-4">
              {tabContent}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Master</DialogTitle>
            <DialogDescription>
              Provide a reason for rejecting{" "}
              {selectedMaster
                ? `${selectedMaster.user.first_name} ${selectedMaster.user.last_name}`
                : "this master"}
              .
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              placeholder="Rejection reason"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setRejectDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleRejectConfirm}
                disabled={!rejectReason.trim()}
              >
                Reject
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Master Details</DialogTitle>
            <DialogDescription>
              Verification details and documents
            </DialogDescription>
          </DialogHeader>
          {selectedMaster && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-muted-foreground">Name</span>
                  <p>
                    {selectedMaster.user.first_name} {selectedMaster.user.last_name}
                  </p>
                </div>
                <div>
                  <span className="font-medium text-muted-foreground">Phone</span>
                  <p>{selectedMaster.user.phone}</p>
                </div>
                <div>
                  <span className="font-medium text-muted-foreground">Category</span>
                  <p>{selectedMaster.category}</p>
                </div>
                <div>
                  <span className="font-medium text-muted-foreground">Status</span>
                  <p>
                    <Badge variant={statusBadgeVariant[selectedMaster.verification_status]}>
                      {selectedMaster.verification_status}
                    </Badge>
                  </p>
                </div>
                {selectedMaster.city && (
                  <div>
                    <span className="font-medium text-muted-foreground">City</span>
                    <p>{selectedMaster.city}</p>
                  </div>
                )}
                {selectedMaster.rating_avg !== undefined && (
                  <div>
                    <span className="font-medium text-muted-foreground">Rating</span>
                    <p>
                      {selectedMaster.rating_avg.toFixed(1)} ({selectedMaster.rating_count} reviews)
                    </p>
                  </div>
                )}
                <div>
                  <span className="font-medium text-muted-foreground">Created</span>
                  <p>{formatDate(selectedMaster.created_at)}</p>
                </div>
              </div>

              {selectedMaster.verification_docs.length > 0 && (
                <div>
                  <span className="font-medium text-muted-foreground text-sm">
                    Verification Documents ({selectedMaster.verification_docs.length})
                  </span>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    {selectedMaster.verification_docs.map((doc, index) => (
                      <a
                        key={index}
                        href={doc}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block rounded-md border p-2 text-sm text-blue-600 hover:bg-muted truncate"
                      >
                        Document {index + 1}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {selectedMaster.verification_status === "pending" && (
                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    variant="destructive"
                    onClick={() => {
                      setViewDialogOpen(false);
                      handleRejectClick(selectedMaster);
                    }}
                  >
                    <X className="h-4 w-4 mr-1" />
                    Reject
                  </Button>
                  <Button
                    onClick={() => {
                      handleApprove(selectedMaster.master_id);
                      setViewDialogOpen(false);
                    }}
                  >
                    <Check className="h-4 w-4 mr-1" />
                    Approve
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
