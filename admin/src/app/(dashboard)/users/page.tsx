"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import api from "@/lib/api";
import { User, PaginatedResponse } from "@/types";
import { Input } from "@/components/ui/input";
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
import { Search, Shield, ShieldOff } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";

const PAGE_SIZE = 20;

const roleBadgeVariant: Record<string, "default" | "info" | "secondary"> = {
  admin: "default",
  master: "info",
  client: "secondary",
};

export default function UsersPage() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedResponse<User> | null>(null);
  const [loading, setLoading] = useState(true);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const [confirmUser, setConfirmUser] = useState<User | null>(null);
  const [roleDialogUser, setRoleDialogUser] = useState<User | null>(null);
  const [newRole, setNewRole] = useState<string>("");

  const handleSearchChange = useCallback((value: string) => {
    setSearch(value);
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      setDebouncedSearch(value);
      setPage(1);
    }, 300);
  }, []);

  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number | boolean> = {
        page,
        page_size: PAGE_SIZE,
      };
      if (debouncedSearch) {
        params.search = debouncedSearch;
      }
      if (roleFilter !== "all") {
        params.role = roleFilter;
      }
      if (statusFilter !== "all") {
        params.is_active = statusFilter === "active";
      }
      const response = await api.get<PaginatedResponse<User>>("/admin/users", {
        params,
      });
      setData(response.data);
    } catch {
      toast.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch, roleFilter, statusFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleToggleActive = async (user: User) => {
    const newStatus = !user.is_active;
    try {
      await api.patch(`/admin/users/${user.id}`, { is_active: newStatus });
      toast.success(
        newStatus
          ? `${user.first_name} ${user.last_name} unblocked`
          : `${user.first_name} ${user.last_name} blocked`
      );
      setConfirmUser(null);
      fetchUsers();
    } catch {
      toast.error("Failed to update user status");
    }
  };

  const handleRoleChange = async () => {
    if (!roleDialogUser || !newRole) return;
    try {
      await api.patch(`/admin/users/${roleDialogUser.id}`, { role: newRole });
      toast.success(
        `${roleDialogUser.first_name} ${roleDialogUser.last_name} role changed to ${newRole}`
      );
      setRoleDialogUser(null);
      setNewRole("");
      fetchUsers();
    } catch {
      toast.error("Failed to change user role");
    }
  };

  const handleRoleFilterChange = (value: string) => {
    setRoleFilter(value);
    setPage(1);
  };

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Users</h1>
        <p className="text-gray-500">Manage platform users</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by name, email, or phone..."
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={roleFilter} onValueChange={handleRoleFilterChange}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All roles</SelectItem>
                <SelectItem value="client">Client</SelectItem>
                <SelectItem value="master">Master</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={handleStatusFilterChange}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="blocked">Blocked</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Phone</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>City</TableHead>
                  <TableHead>Registered</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                      Loading...
                    </TableCell>
                  </TableRow>
                ) : !data || data.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                      No users found
                    </TableCell>
                  </TableRow>
                ) : (
                  data.items.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">
                        {user.first_name} {user.last_name}
                      </TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>{user.phone}</TableCell>
                      <TableCell>
                        <Badge variant={roleBadgeVariant[user.role]}>
                          {user.role}
                        </Badge>
                      </TableCell>
                      <TableCell>{user.city || "—"}</TableCell>
                      <TableCell>{formatDate(user.created_at)}</TableCell>
                      <TableCell>
                        {user.is_active ? (
                          <Badge variant="success">Active</Badge>
                        ) : (
                          <Badge variant="destructive">Blocked</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setRoleDialogUser(user);
                              setNewRole(user.role);
                            }}
                          >
                            Change Role
                          </Button>
                          <Button
                            variant={user.is_active ? "destructive" : "outline"}
                            size="sm"
                            onClick={() => setConfirmUser(user)}
                          >
                            {user.is_active ? (
                              <>
                                <ShieldOff className="h-4 w-4 mr-1" />
                                Block
                              </>
                            ) : (
                              <>
                                <Shield className="h-4 w-4 mr-1" />
                                Unblock
                              </>
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {data && (
            <Pagination
              page={page}
              totalPages={data.pages}
              onPageChange={setPage}
            />
          )}
        </CardContent>
      </Card>

      {/* Block/Unblock Confirmation Dialog */}
      <Dialog open={!!confirmUser} onOpenChange={() => setConfirmUser(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {confirmUser?.is_active ? "Block User" : "Unblock User"}
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to {confirmUser?.is_active ? "block" : "unblock"}{" "}
              {confirmUser?.first_name} {confirmUser?.last_name}?
              {confirmUser?.is_active &&
                " This user will lose access to the platform immediately."}
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setConfirmUser(null)}>
              Cancel
            </Button>
            <Button
              variant={confirmUser?.is_active ? "destructive" : "default"}
              onClick={() => confirmUser && handleToggleActive(confirmUser)}
            >
              {confirmUser?.is_active ? "Block" : "Unblock"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Change Role Dialog */}
      <Dialog open={!!roleDialogUser} onOpenChange={() => setRoleDialogUser(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change User Role</DialogTitle>
            <DialogDescription>
              Change role for {roleDialogUser?.first_name} {roleDialogUser?.last_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Select value={newRole} onValueChange={setNewRole}>
              <SelectTrigger>
                <SelectValue placeholder="Select role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="client">Client</SelectItem>
                <SelectItem value="master">Master</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setRoleDialogUser(null)}>
                Cancel
              </Button>
              <Button
                onClick={handleRoleChange}
                disabled={newRole === roleDialogUser?.role}
              >
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
