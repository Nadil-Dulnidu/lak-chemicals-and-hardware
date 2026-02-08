// API Types for LAK Chemicals and Hardware

// ============= Enums =============
export type ProductCategory =
  | "chemicals"
  | "hardware"
  | "tools"
  | "paints"
  | "electrical"
  | "plumbing"
  | "building_materials"
  | "safety_equipment"
  | "other";

export type OrderStatus = "PENDING" | "COMPLETED" | "CANCELLED";
export type QuotationStatus = "PENDING" | "APPROVED" | "REJECTED";
export type ReportType = "SALES" | "INVENTORY" | "PRODUCT_PERFORMANCE" | "LOW_STOCK";

// ============= Product Types =============
export interface Product {
  id: string;
  name: string;
  price: number;
  stock_qty: number;
  category: ProductCategory;
  brand?: string;
  description?: string;
  image_url?: string;
  reorder_level: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  name: string;
  price: number;
  stock_qty: number;
  category?: ProductCategory;
  brand?: string;
  description?: string;
  image_url?: string;
  reorder_level?: number;
}

export interface ProductUpdate {
  name?: string;
  price?: number;
  stock_qty?: number;
  category?: ProductCategory;
  brand?: string;
  description?: string;
  image_url?: string;
  reorder_level?: number;
  is_active?: boolean;
}

export interface ProductListResponse {
  products: Product[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface LowStockAlert {
  product_id: string;
  product_name: string;
  current_stock: number;
  reorder_level: number;
  priority: "critical" | "high" | "medium" | "low";
  quantity_needed: number;
}

// ============= Cart Types =============
export interface CartItem {
  cart_item_id: number;
  product_id: string;
  product_name?: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Cart {
  cart_id: number;
  user_id: string;
  items: CartItem[];
  total_items: number;
  total_amount: number;
}

export interface CartItemCreate {
  product_id: string;
  quantity: number;
}

export interface CartItemUpdate {
  quantity: number;
}

export interface CartSummary {
  total_items: number;
  total_amount: number;
}

// ============= Quotation Types =============
export interface QuotationItem {
  quotation_item_id: number;
  product_id: string;
  product_name?: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Quotation {
  quotation_id: number;
  user_id: string;
  status: QuotationStatus;
  total_amount: number;
  notes?: string;
  created_at: string;
  items: QuotationItem[];
}

export interface QuotationCreate {
  items: { product_id: string; quantity: number }[];
  notes?: string;
}

export interface QuotationFromCart {
  notes?: string;
}

export interface QuotationListResponse {
  quotations: Quotation[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

// ============= Order Types =============
export interface OrderItem {
  order_item_id: number;
  product_id: string;
  product_name?: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Order {
  order_id: number;
  user_id: string;
  quotation_id?: number;
  status: OrderStatus;
  total_amount: number;
  payment_method?: string;
  order_date: string;
  completed_date?: string;
  cancelled_date?: string;
  notes?: string;
  items: OrderItem[];
}

export interface OrderCreate {
  items: { product_id: string; quantity: number }[];
  payment_method?: string;
  notes?: string;
}

export interface OrderFromQuotation {
  quotation_id: number;
  payment_method?: string;
  notes?: string;
}

export interface OrderListResponse {
  orders: Order[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

// ============= Sales Types =============
export interface Sale {
  sale_id: number;
  order_id: number;
  product_id: string;
  product_name?: string;
  quantity: number;
  revenue: number;
  sale_date: string;
}

export interface SalesListResponse {
  sales: Sale[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface SalesSummary {
  total_sales: number;
  total_revenue: number;
  start_date?: string;
  end_date?: string;
}

// ============= Report Types =============
export interface Report {
  report_id: number;
  report_name: string;
  report_type: ReportType;
  parameters?: Record<string, unknown>;
  created_by: string;
  created_at: string;
  updated_at: string;
  description?: string;
}

export interface ReportCreate {
  report_name: string;
  report_type: ReportType;
  parameters?: Record<string, unknown>;
  description?: string;
}

export interface SalesReportData {
  report_type: string;
  start_date: string;
  end_date: string;
  summary: {
    total_sales: number;
    total_revenue: number;
    total_quantity: number;
    average_sale_value: number;
  };
  items: {
    period: string;
    total_sales: number;
    total_revenue: number;
    total_quantity: number;
  }[];
  product_breakdown?: {
    product_id: string;
    product_name: string;
    quantity_sold: number;
    revenue: number;
    sales_count: number;
  }[];
  category_breakdown?: {
    category: string;
    quantity_sold: number;
    revenue: number;
    sales_count: number;
  }[];
}

export interface InventoryReportData {
  report_type: string;
  generated_at: string;
  summary: {
    total_products: number;
    total_stock_value: number;
    low_stock_count: number;
    out_of_stock_count: number;
  };
  items: {
    product_id: string;
    product_name: string;
    category: string;
    current_stock: number;
    reorder_level: number;
    stock_value: number;
    status: "OK" | "LOW" | "OUT_OF_STOCK";
  }[];
  low_stock_items: {
    product_id: string;
    product_name: string;
    category: string;
    current_stock: number;
    reorder_level: number;
    stock_value: number;
    status: "OK" | "LOW" | "OUT_OF_STOCK";
  }[];
}

// ============= Supplier Types =============
export interface Supplier {
  id: string;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupplierCreate {
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
}

export interface SupplierListResponse {
  suppliers: Supplier[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

// ============= Payment Types =============
export interface PaymentIntentCreate {
  amount: number;
}

export interface PaymentIntentResponse {
  client_secret: string;
}

// ============= API Response Types =============
export interface ApiError {
  detail: string;
}
