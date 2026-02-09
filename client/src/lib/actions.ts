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
  ReportConfig,
  ReportConfigListResponse,
  StockMovement,
  StockMovementCreate,
  StockMovementListResponse,
  InventoryLevel,
  StockAdjustment,
} from "./types";

// ============= Product Actions =============
export const productActions = {
  getAll: (skip = 0, limit = 100, includeInactive = false) =>
    apiClient<ProductListResponse>(
      `/products?skip=${skip}&limit=${limit}&include_inactive=${includeInactive}`,
    ),

  getById: (id: string) => apiClient<Product>(`/products/${id}`),

  // Create product with optional image
  create: (data: ProductCreate, image?: File, token?: string | null) => {
    const formData = new FormData();
    formData.append("name", data.name);
    formData.append("price", data.price.toString());
    formData.append("stock_qty", data.stock_qty.toString());
    if (data.category) formData.append("category", data.category);
    if (data.brand) formData.append("brand", data.brand);
    if (data.description) formData.append("description", data.description);
    if (data.reorder_level !== undefined) formData.append("reorder_level", data.reorder_level.toString());
    if (image) formData.append("image", image);

    return apiClientFormData<Product>("/products/", formData, "POST", { token });
  },

  update: (id: string, data: ProductUpdate, token?: string | null) =>
    apiClient<Product>(`/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (id: string, hard = false, token?: string | null) =>
    apiClient<void>(`/products/${id}?hard=${hard}`, {
      method: "DELETE",
      token,
    }),

  search: (q: string, skip = 0, limit = 100) =>
    apiClient<ProductListResponse>(
      `/products/search/query?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`
    ),

  getByCategory: (category: ProductCategory, skip = 0, limit = 100) =>
    apiClient<ProductListResponse>(
      `/products/category/${category}?skip=${skip}&limit=${limit}`
    ),

  getLowStockAlerts: (threshold = 10, limit = 100, token?: string | null) =>
    apiClient<LowStockAlert[]>(
      `/products/alerts/low-stock?threshold=${threshold}&limit=${limit}`,
      { token }
    ),
};

// ============= Cart Actions =============
export const cartActions = {
  get: (token?: string | null) => apiClient<Cart>("/cart/items", { token }),

  getSummary: (token?: string | null) => apiClient<CartSummary>("/cart/summary", { token }),

  addItem: (data: CartItemCreate, token?: string | null) =>
    apiClient<Cart>("/cart/items", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateItem: (cartItemId: number, data: CartItemUpdate, token?: string | null) =>
    apiClient<Cart>(`/cart/items/${cartItemId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  removeItem: (cartItemId: number, token?: string | null) =>
    apiClient<void>(`/cart/items/${cartItemId}`, {
      method: "DELETE",
      token,
    }),

  clear: (token?: string | null) =>
    apiClient<void>("/cart", {
      method: "DELETE",
      token,
    }),
};

// ============= Inventory Actions =============
export const inventoryActions = {
  // Record stock movement (IN or OUT)
  recordMovement: (data: StockMovementCreate, token?: string | null) =>
    apiClient<StockMovement>("/inventory/stock-update", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Get single movement by ID
  getMovement: (movementId: number, token?: string | null) =>
    apiClient<StockMovement>(`/inventory/movements/${movementId}`, { token }),

  // Get all movements with pagination
  getAllMovements: (skip = 0, limit = 100, token?: string | null) =>
    apiClient<StockMovementListResponse>(`/inventory/movements?skip=${skip}&limit=${limit}`, { token }),

  // Filter movements
  filterMovements: (params: {
    product_id?: string;
    movement_type?: "IN" | "OUT";
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }, token?: string | null) =>
    apiClient<StockMovementListResponse>("/inventory/movements/filter", {
      method: "POST",
      body: JSON.stringify(params),
      token,
    }),

  // Get movements for a specific product
  getProductMovements: (productId: string, skip = 0, limit = 100, token?: string | null) =>
    apiClient<StockMovementListResponse>(`/inventory/product/${productId}/movements?skip=${skip}&limit=${limit}`, { token }),

  // Get current inventory level for a product
  getInventoryLevel: (productId: string, token?: string | null) =>
    apiClient<InventoryLevel>(`/inventory/product/${productId}/level`, { token }),

  // Delete a movement record
  deleteMovement: (movementId: number, token?: string | null) =>
    apiClient<void>(`/inventory/movements/${movementId}`, {
      method: "DELETE",
      token,
    }),

  // Adjust stock to a target quantity
  adjustStock: (data: StockAdjustment, token?: string | null) =>
    apiClient<StockMovement>("/inventory/adjust", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),
};

// ============= Quotation Actions =============
export const quotationActions = {
  getAll: (skip = 0, limit = 100, token?: string | null) =>
    apiClient<QuotationListResponse>(`/quotations?skip=${skip}&limit=${limit}`, { token }),

  getById: (id: number, token?: string | null) => apiClient<Quotation>(`/quotations/${id}`, { token }),

  getByUserId: (token: string | null, userId: string | null, skip = 0, limit = 100) =>
    apiClient<QuotationListResponse>(`/quotations/user/${userId}?skip=${skip}&limit=${limit}`, { token }),

  create: (data: QuotationCreate, token?: string | null) =>
    apiClient<Quotation>("/quotations", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  createFromCart: (data: QuotationFromCart, token?: string | null) =>
    apiClient<Quotation>("/quotations/from-cart", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateStatus: (id: number, status: "PENDING" | "APPROVED" | "REJECTED", token?: string | null) =>
    apiClient<Quotation>(`/quotations/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
      token,
    }),

  delete: (id: number, token?: string | null) =>
    apiClient<void>(`/quotations/${id}`, {
      method: "DELETE",
      token,
    }),

  filter: (params: {
    status?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }, token?: string | null) =>
    apiClient<QuotationListResponse>("/quotations/filter", {
      method: "POST",
      body: JSON.stringify(params),
      token,
    }),
};

// ============= Order Actions =============
export const orderActions = {
  getAll: (skip = 0, limit = 100, token?: string | null) =>
    apiClient<OrderListResponse>(`/orders?skip=${skip}&limit=${limit}`, { token }),

  getById: (id: number, token?: string | null) => apiClient<Order>(`/orders/${id}`, { token }),

  getByUserId: (userId: string | undefined, skip = 0, limit = 100, token: string | null) =>
    apiClient<OrderListResponse>(`/orders/user/${userId}?skip=${skip}&limit=${limit}`, { token }),

  create: (data: OrderCreate, token?: string | null) =>
    apiClient<Order>("/orders", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateStatus: (id: number, status: "PENDING" | "COMPLETED" | "CANCELLED", token?: string | null) =>
    apiClient<Order>(`/orders/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
      token,
    }),

  delete: (id: number, token?: string | null) =>
    apiClient<void>(`/orders/${id}`, {
      method: "DELETE",
      token,
    }),

  filter: (params: {
    status?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }, token?: string | null) =>
    apiClient<OrderListResponse>("/orders/filter", {
      method: "POST",
      body: JSON.stringify(params),
      token,
    }),
};

// ============= Sales Actions =============
// ============= Sales Actions =============
export const salesActions = {
  getAll: (skip = 0, limit = 100, token?: string | null) =>
    apiClient<SalesListResponse>(`/orders/sales?skip=${skip}&limit=${limit}`, { token }),

  getSummary: (params?: {
    product_id?: string;
    start_date?: string;
    end_date?: string;
  }, token?: string | null) =>
    apiClient<SalesSummary>("/orders/sales/summary", {
      method: "POST",
      body: JSON.stringify(params || {}),
      token,
    }),

  filter: (params: {
    product_id?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }, token?: string | null) =>
    apiClient<SalesListResponse>("/orders/sales/filter", {
      method: "POST",
      body: JSON.stringify(params),
      token,
    }),
};

// ============= Report Actions =============
// ============= Report Actions =============
export const reportActions = {
  generateSales: (params: {
    start_date: string;
    end_date: string;
    product_id?: string;
    category?: string;
    group_by?: "day" | "week" | "month";
  }, token?: string | null) =>
    apiClient<SalesReportData>("/reports/generate/sales", {
      method: "POST",
      body: JSON.stringify(params),
      token,
    }),

  generateInventory: (params?: { category?: string; low_stock_only?: boolean }, token?: string | null) =>
    apiClient<InventoryReportData>("/reports/generate/inventory", {
      method: "POST",
      body: JSON.stringify(params || {}),
      token,
    }),

  generateProductPerformance: (params: {
    start_date: string;
    end_date: string;
    category?: string;
    top_n?: number;
  }, token?: string | null) =>
    apiClient("/reports/generate/product-performance", {
      method: "POST",
      body: JSON.stringify(params),
      token,
    }),

  generateLowStock: (params?: { category?: string; threshold_percentage?: number }, token?: string | null) =>
    apiClient("/reports/generate/low-stock", {
      method: "POST",
      body: JSON.stringify(params || {}),
      token,
    }),

  // ============= Report Configuration CRUD =============

  // Create a saved report configuration
  create: (data: {
    report_name: string;
    report_type: "SALES" | "INVENTORY" | "PRODUCT_PERFORMANCE" | "LOW_STOCK";
    parameters?: Record<string, unknown>;
    description?: string;
  }, token?: string | null) =>
    apiClient<ReportConfig>("/reports", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Get all saved report configurations
  getAll: (skip = 0, limit = 100, token?: string | null) =>
    apiClient<ReportConfigListResponse>(`/reports?skip=${skip}&limit=${limit}`, { token }),

  // Get a single report configuration by ID
  getById: (id: number, token?: string | null) => apiClient<ReportConfig>(`/reports/${id}`, { token }),

  // Update a report configuration
  update: (id: number, data: {
    report_name?: string;
    parameters?: Record<string, unknown>;
    description?: string;
  }, token?: string | null) =>
    apiClient<ReportConfig>(`/reports/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      token,
    }),

  // Delete a report configuration
  delete: (id: number, token?: string | null) =>
    apiClient<void>(`/reports/${id}`, {
      method: "DELETE",
      token,
    }),

  // Run a saved report configuration
  run: (id: number, overrides?: {
    start_date?: string;
    end_date?: string;
    category?: string;
    product_id?: string;
    group_by?: string;
    top_n?: number;
    threshold_percentage?: number;
    low_stock_only?: boolean;
  }, token?: string | null) =>
    apiClient<Record<string, unknown>>(`/reports/${id}/run`, {
      method: "POST",
      body: JSON.stringify(overrides || {}),
      token,
    }),
};

// ============= Supplier Actions =============
// ============= Supplier Actions =============
export const supplierActions = {
  getAll: (skip = 0, limit = 100, token?: string | null) =>
    apiClient<SupplierListResponse>(`/suppliers?skip=${skip}&limit=${limit}`, { token }),

  getById: (id: string, token?: string | null) => apiClient<Supplier>(`/suppliers/${id}`, { token }),

  create: (data: SupplierCreate, token?: string | null) =>
    apiClient<Supplier>("/suppliers/", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (id: string, data: Partial<SupplierCreate>, token?: string | null) =>
    apiClient<Supplier>(`/suppliers/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (id: string, token?: string | null) =>
    apiClient<void>(`/suppliers/${id}`, {
      method: "DELETE",
      token,
    }),

  // Link a product to a supplier
  linkProduct: (supplierId: string, productId: string, supplyPrice?: number, token?: string | null) =>
    apiClient<{ message: string }>(`/suppliers/${supplierId}/products`, {
      method: "POST",
      body: JSON.stringify({ product_id: productId, supply_price: supplyPrice }),
      token,
    }),

  // Unlink a product from a supplier
  unlinkProduct: (supplierId: string, productId: string, token?: string | null) =>
    apiClient<void>(`/suppliers/${supplierId}/products/${productId}`, {
      method: "DELETE",
      token,
    }),

  // Get supplier with product details
  getDetail: (id: string, token?: string | null) =>
    apiClient<Supplier & { products: { product_id: string; product_name: string; supply_price?: number }[] }>(
      `/suppliers/${id}/detail`,
      { token }
    ),
};

// ============= Payment Actions =============
export const paymentActions = {
  createPaymentIntent: (data: PaymentIntentCreate, token?: string | null) =>
    apiClient<PaymentIntentResponse>("/payments/create-payment-intent", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  createCheckout: (orderId: number, token?: string | null) =>
    apiClient<{ checkout_url: string }>(`/payments/create-checkout-session/${orderId}`, {
      method: "POST",
      token,
    }),

  getPaymentStatus: (orderId: number, token?: string | null) =>
    apiClient<{ payment_status: string; payment_intent_id?: string }>(`/payments/status/${orderId}`, { token }),
};
