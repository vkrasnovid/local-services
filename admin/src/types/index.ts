export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DashboardStats {
  users: {
    total: number;
    new_today: number;
    new_this_week: number;
    by_role: {
      client: number;
      master: number;
      admin: number;
    };
  };
  bookings: {
    total: number;
    active: number;
    completed_this_week: number;
    cancelled_this_week: number;
  };
  revenue: {
    total: number;
    this_week: number;
    platform_fees_total: number;
    platform_fees_this_week: number;
  };
  masters_pending_verification: number;
  reviews_pending_moderation: number;
}

export interface User {
  id: string;
  phone: string;
  email: string;
  first_name: string;
  last_name: string;
  role: "client" | "master" | "admin";
  city: string;
  is_active: boolean;
  avatar_url: string | null;
  created_at: string;
}

export interface MasterVerification {
  master_id: string;
  user: {
    id: string;
    first_name: string;
    last_name: string;
    phone: string;
  };
  category: string;
  city?: string;
  rating_avg?: number;
  rating_count?: number;
  verification_status: "pending" | "verified" | "rejected";
  verification_docs: string[];
  created_at: string;
}

export interface Booking {
  id: string;
  client: { id: string; first_name: string; last_name: string };
  master: { id: string; user: { first_name: string; last_name: string } };
  service: { name: string; price: number };
  slot?: { date: string; start_time: string };
  status: "pending" | "confirmed" | "in_progress" | "completed" | "cancelled";
  price: number;
  address?: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  booking_id: string;
  client_name: string;
  master_name: string;
  service_name: string;
  amount: number;
  platform_fee: number;
  master_amount: number;
  status: "pending" | "waiting_for_capture" | "succeeded" | "cancelled" | "refunded";
  paid_at: string;
}

export interface TransactionsResponse extends PaginatedResponse<Transaction> {
  totals: {
    amount: number;
    platform_fees: number;
  };
}

export interface Review {
  id: string;
  client: { id: string; first_name: string };
  master: { id: string; user: { first_name: string } };
  rating: number;
  text: string;
  is_visible: boolean;
  created_at: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  icon: string;
  sort_order: number;
  is_active: boolean;
}
