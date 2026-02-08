// API Actions for LAK Chemicals and Hardware
import { apiClient, apiClientFormData } from "./api";
import type {
  Product,
  ProductCreate,
  ProductUpdate,
  ProductListResponse,
  ProductCategory,
  LowStockAlert,
  Cart,
  CartItemCreate,
  CartItemUpdate,
  CartSummary,
  Quotation,
  QuotationCreate,
  QuotationFromCart,
  QuotationListResponse,
  Order,
  OrderCreate,
  OrderListResponse,
  SalesListResponse,
  SalesSummary,
  Supplier,
  SupplierCreate,
  SupplierListResponse,
  SalesReportData,
  InventoryReportData,
  PaymentIntentCreate,
  PaymentIntentResponse,
} from "./types";

// ============= Product Actions =============
export const productActions = {
  getAll: (skip = 0, limit = 100, includeInactive = false) =>
    apiClient<ProductListResponse>(
      `/products?skip=${skip}&limit=${limit}&include_inactive=${includeInactive}`
    ),

  getById: (id: string) => apiClient<Product>(`/products/${id}`),

  // Create product with optional image
  create: (data: ProductCreate, image?: File) => {
    const formData = new FormData();
    formData.append("name", data.name);
    formData.append("price", data.price.toString());
    formData.append("stock_qty", data.stock_qty.toString());
    if (data.category) formData.append("category", data.category);
    if (data.brand) formData.append("brand", data.brand);
    if (data.description) formData.append("description", data.description);
    if (data.reorder_level !== undefined) formData.append("reorder_level", data.reorder_level.toString());
    if (image) formData.append("image", image);

    return apiClientFormData<Product>("/products/", formData);
  },

  update: (id: string, data: ProductUpdate) =>
    apiClient<Product>(`/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string, hard = false) =>
    apiClient<void>(`/products/${id}?hard=${hard}`, {
      method: "DELETE",
    }),

  search: (q: string, skip = 0, limit = 100) =>
    apiClient<ProductListResponse>(
      `/products/search/query?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`
    ),

  getByCategory: (category: ProductCategory, skip = 0, limit = 100) =>
    apiClient<ProductListResponse>(
      `/products/category/${category}?skip=${skip}&limit=${limit}`
    ),

  getLowStockAlerts: (threshold = 10, limit = 100) =>
    apiClient<LowStockAlert[]>(
      `/products/alerts/low-stock?threshold=${threshold}&limit=${limit}`
    ),
};

// ============= Cart Actions =============
export const cartActions = {
  get: () => apiClient<Cart>("/cart"),

  getSummary: () => apiClient<CartSummary>("/cart/summary"),

  addItem: (data: CartItemCreate) =>
    apiClient<Cart>("/cart/items", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateItem: (cartItemId: number, data: CartItemUpdate) =>
    apiClient<Cart>(`/cart/items/${cartItemId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  removeItem: (cartItemId: number) =>
    apiClient<void>(`/cart/items/${cartItemId}`, {
      method: "DELETE",
    }),

  clear: () =>
    apiClient<void>("/cart", {
      method: "DELETE",
    }),
};

// ============= Quotation Actions =============
export const quotationActions = {
  getAll: (skip = 0, limit = 100) =>
    apiClient<QuotationListResponse>(`/quotations?skip=${skip}&limit=${limit}`),

  getById: (id: number) => apiClient<Quotation>(`/quotations/${id}`),

  create: (data: QuotationCreate) =>
    apiClient<Quotation>("/quotations", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  createFromCart: (data: QuotationFromCart) =>
    apiClient<Quotation>("/quotations/from-cart", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateStatus: (id: number, status: "PENDING" | "APPROVED" | "REJECTED") =>
    apiClient<Quotation>(`/quotations/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  delete: (id: number) =>
    apiClient<void>(`/quotations/${id}`, {
      method: "DELETE",
    }),

  filter: (params: {
    status?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }) =>
    apiClient<QuotationListResponse>("/quotations/filter", {
      method: "POST",
      body: JSON.stringify(params),
    }),
};

// ============= Order Actions =============
export const orderActions = {
  getAll: (skip = 0, limit = 100) =>
    apiClient<OrderListResponse>(`/orders?skip=${skip}&limit=${limit}`),

  getById: (id: number) => apiClient<Order>(`/orders/${id}`),

  create: (data: OrderCreate) =>
    apiClient<Order>("/orders", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateStatus: (id: number, status: "PENDING" | "COMPLETED" | "CANCELLED") =>
    apiClient<Order>(`/orders/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  delete: (id: number) =>
    apiClient<void>(`/orders/${id}`, {
      method: "DELETE",
    }),

  filter: (params: {
    status?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }) =>
    apiClient<OrderListResponse>("/orders/filter", {
      method: "POST",
      body: JSON.stringify(params),
    }),
};

// ============= Sales Actions =============
export const salesActions = {
  getAll: (skip = 0, limit = 100) =>
    apiClient<SalesListResponse>(`/orders/sales?skip=${skip}&limit=${limit}`),

  getSummary: (params?: {
    product_id?: string;
    start_date?: string;
    end_date?: string;
  }) =>
    apiClient<SalesSummary>("/orders/sales/summary", {
      method: "POST",
      body: JSON.stringify(params || {}),
    }),

  filter: (params: {
    product_id?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }) =>
    apiClient<SalesListResponse>("/orders/sales/filter", {
      method: "POST",
      body: JSON.stringify(params),
    }),
};

// ============= Report Actions =============
export const reportActions = {
  generateSales: (params: {
    start_date: string;
    end_date: string;
    product_id?: string;
    category?: string;
    group_by?: "day" | "week" | "month";
  }) =>
    apiClient<SalesReportData>("/reports/generate/sales", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  generateInventory: (params?: { category?: string; low_stock_only?: boolean }) =>
    apiClient<InventoryReportData>("/reports/generate/inventory", {
      method: "POST",
      body: JSON.stringify(params || {}),
    }),

  generateProductPerformance: (params: {
    start_date: string;
    end_date: string;
    category?: string;
    top_n?: number;
  }) =>
    apiClient("/reports/generate/product-performance", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  generateLowStock: (params?: { category?: string; threshold_percentage?: number }) =>
    apiClient("/reports/generate/low-stock", {
      method: "POST",
      body: JSON.stringify(params || {}),
    }),
};

// ============= Supplier Actions =============
export const supplierActions = {
  getAll: (skip = 0, limit = 100) =>
    apiClient<SupplierListResponse>(`/suppliers?skip=${skip}&limit=${limit}`),

  getById: (id: string) => apiClient<Supplier>(`/suppliers/${id}`),

  create: (data: SupplierCreate) =>
    apiClient<Supplier>("/suppliers/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<SupplierCreate>) =>
    apiClient<Supplier>(`/suppliers/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiClient<void>(`/suppliers/${id}`, {
      method: "DELETE",
    }),

  // Link a product to a supplier
  linkProduct: (supplierId: string, productId: string, supplyPrice?: number) =>
    apiClient<{ message: string }>(`/suppliers/${supplierId}/products`, {
      method: "POST",
      body: JSON.stringify({ product_id: productId, supply_price: supplyPrice }),
    }),

  // Unlink a product from a supplier
  unlinkProduct: (supplierId: string, productId: string) =>
    apiClient<void>(`/suppliers/${supplierId}/products/${productId}`, {
      method: "DELETE",
    }),

  // Get supplier with product details
  getDetail: (id: string) =>
    apiClient<Supplier & { products: { product_id: string; product_name: string; supply_price?: number }[] }>(
      `/suppliers/${id}/detail`
    ),
};

// ============= Payment Actions =============
export const paymentActions = {
  createPaymentIntent: (data: PaymentIntentCreate) =>
    apiClient<PaymentIntentResponse>("/payments/create-payment-intent", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  createCheckout: (orderId: number) =>
    apiClient<{ checkout_url: string }>(`/payments/create-checkout-session/${orderId}`, {
      method: "POST",
    }),

  getPaymentStatus: (orderId: number) =>
    apiClient<{ payment_status: string; payment_intent_id?: string }>(`/payments/status/${orderId}`),
};
