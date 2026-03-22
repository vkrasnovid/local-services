"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { Review, PaginatedResponse } from "@/types";
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
import { Pagination } from "@/components/pagination";
import { Eye, EyeOff, Star } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";

const PAGE_SIZE = 20;

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }, (_, i) => (
        <Star
          key={i}
          className="h-4 w-4"
          fill={i < rating ? "#F4A236" : "none"}
          color={i < rating ? "#F4A236" : "#d1d5db"}
        />
      ))}
    </div>
  );
}

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [visibilityFilter, setVisibilityFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const [confirmReview, setConfirmReview] = useState<Review | null>(null);

  const fetchReviews = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: PAGE_SIZE,
      };
      if (visibilityFilter === "visible") {
        params.is_visible = 1;
      } else if (visibilityFilter === "hidden") {
        params.is_visible = 0;
      }

      const { data } = await api.get<PaginatedResponse<Review>>(
        "/admin/reviews",
        { params }
      );
      setReviews(data.items);
      setTotalPages(data.pages);
      setTotal(data.total);
    } catch {
      toast.error("Failed to load reviews");
    } finally {
      setLoading(false);
    }
  }, [page, visibilityFilter]);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  const handleFilterChange = (value: string) => {
    setVisibilityFilter(value);
    setPage(1);
  };

  const toggleVisibility = async (review: Review) => {
    setConfirmReview(null);
    setTogglingId(review.id);
    try {
      await api.patch(`/admin/reviews/${review.id}`, {
        is_visible: !review.is_visible,
      });
      setReviews((prev) =>
        prev.map((r) =>
          r.id === review.id ? { ...r, is_visible: !r.is_visible } : r
        )
      );
      toast.success(
        review.is_visible ? "Review hidden" : "Review is now visible"
      );
    } catch {
      toast.error("Failed to update review visibility");
    } finally {
      setTogglingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Reviews</h1>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Filter:</span>
          <Select value={visibilityFilter} onValueChange={handleFilterChange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by visibility" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Show all</SelectItem>
              <SelectItem value="visible">Show visible only</SelectItem>
              <SelectItem value="hidden">Show hidden only</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {total} review{total !== 1 ? "s" : ""}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              Loading...
            </div>
          ) : reviews.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              No reviews found
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Client Name</TableHead>
                    <TableHead>Master Name</TableHead>
                    <TableHead>Rating</TableHead>
                    <TableHead className="max-w-[300px]">Review Text</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reviews.map((review) => (
                    <TableRow key={review.id}>
                      <TableCell>{review.client.first_name}</TableCell>
                      <TableCell>{review.master.user.first_name}</TableCell>
                      <TableCell>
                        <StarRating rating={review.rating} />
                      </TableCell>
                      <TableCell className="max-w-[300px]">
                        <span className="line-clamp-2">
                          {review.text.length > 100
                            ? `${review.text.slice(0, 100)}...`
                            : review.text}
                        </span>
                      </TableCell>
                      <TableCell>
                        {review.is_visible ? (
                          <Badge variant="default">Visible</Badge>
                        ) : (
                          <Badge variant="secondary">Hidden</Badge>
                        )}
                      </TableCell>
                      <TableCell>{formatDate(review.created_at)}</TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setConfirmReview(review)}
                          disabled={togglingId === review.id}
                        >
                          {review.is_visible ? (
                            <>
                              <EyeOff className="mr-1 h-4 w-4" />
                              Hide
                            </>
                          ) : (
                            <>
                              <Eye className="mr-1 h-4 w-4" />
                              Show
                            </>
                          )}
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

      {/* Visibility Confirmation Dialog */}
      <Dialog open={!!confirmReview} onOpenChange={() => setConfirmReview(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {confirmReview?.is_visible ? "Hide Review" : "Show Review"}
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to {confirmReview?.is_visible ? "hide" : "show"}{" "}
              this review from {confirmReview?.client.first_name}?
              {confirmReview?.is_visible &&
                " It will no longer be visible to users on the platform."}
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setConfirmReview(null)}>
              Cancel
            </Button>
            <Button
              variant={confirmReview?.is_visible ? "destructive" : "default"}
              onClick={() => confirmReview && toggleVisibility(confirmReview)}
            >
              {confirmReview?.is_visible ? "Hide" : "Show"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
