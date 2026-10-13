package com.lakchemicals.business.controller;

import com.lakchemicals.business.constants.ProductCategory;
import com.lakchemicals.business.dto.product.*;
import com.lakchemicals.business.security.SecurityUtils;
import com.lakchemicals.business.service.CloudStorageService;
import com.lakchemicals.business.service.ProductService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Arrays;
import java.util.List;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping({"/api/v1/products", "/products"})
@Tag(name = "Products", description = "Product Management Endpoints")
@RequiredArgsConstructor
public class ProductController {

    private final ProductService productService;
    private final CloudStorageService cloudStorageService;

    @PostMapping(value = {"", "/"}, consumes = {MediaType.MULTIPART_FORM_DATA_VALUE, MediaType.APPLICATION_JSON_VALUE})
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @Operation(summary = "Create a new product with optional image upload")
    public ResponseEntity<ProductResponse> createProduct(
            @RequestParam("name") String name,
            @RequestParam("price") Double price,
            @RequestParam("stock_qty") Integer stockQty,
            @RequestParam(value = "category", required = false) String category,
            @RequestParam(value = "brand", required = false) String brand,
            @RequestParam(value = "description", required = false) String description,
            @RequestParam(value = "reorder_level", required = false, defaultValue = "10") Integer reorderLevel,
            @RequestParam(value = "image", required = false) MultipartFile image
    ) {
        String userId = SecurityUtils.getCurrentUserId();
        String imageUrl = null;
        if (image != null && !image.isEmpty()) {
            imageUrl = cloudStorageService.uploadImage(image);
        }

        ProductCategory productCategory = category != null ? ProductCategory.fromValue(category) : null;

        ProductCreateRequest request = ProductCreateRequest.builder()
                .name(name)
                .price(price)
                .stockQty(stockQty)
                .category(productCategory)
                .brand(brand)
                .description(description)
                .reorderLevel(reorderLevel)
                .imageUrl(imageUrl)
                .build();

        ProductResponse response = productService.createProduct(request, userId);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get a product by ID")
    public ResponseEntity<ProductResponse> getProductById(@PathVariable("id") UUID id) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(productService.getProductById(id, userId));
    }

    @PutMapping(value = "/{id}", consumes = {MediaType.MULTIPART_FORM_DATA_VALUE, MediaType.APPLICATION_JSON_VALUE})
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @Operation(summary = "Update a product with optional image upload")
    public ResponseEntity<ProductResponse> updateProduct(
            @PathVariable("id") UUID id,
            @RequestParam(value = "name", required = false) String name,
            @RequestParam(value = "price", required = false) Double price,
            @RequestParam(value = "stock_qty", required = false) Integer stockQty,
            @RequestParam(value = "category", required = false) String category,
            @RequestParam(value = "brand", required = false) String brand,
            @RequestParam(value = "description", required = false) String description,
            @RequestParam(value = "reorder_level", required = false) Integer reorderLevel,
            @RequestParam(value = "is_active", required = false) Boolean isActive,
            @RequestParam(value = "image", required = false) MultipartFile image
    ) {
        String userId = SecurityUtils.getCurrentUserId();
        String imageUrl = null;
        if (image != null && !image.isEmpty()) {
            imageUrl = cloudStorageService.uploadImage(image);
        }

        ProductCategory productCategory = category != null ? ProductCategory.fromValue(category) : null;

        ProductUpdateRequest request = ProductUpdateRequest.builder()
                .name(name)
                .price(price)
                .stockQty(stockQty)
                .category(productCategory)
                .brand(brand)
                .description(description)
                .reorderLevel(reorderLevel)
                .isActive(isActive)
                .imageUrl(imageUrl)
                .build();

        return ResponseEntity.ok(productService.updateProduct(id, request, userId));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete a product (soft delete)")
    public ResponseEntity<Void> deleteProduct(@PathVariable("id") UUID id) {
        String userId = SecurityUtils.getCurrentUserId();
        productService.deleteProduct(id, userId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping({"", "/"})
    @Operation(summary = "Get all products with filtering and pagination")
    public ResponseEntity<ProductListResponse> getProducts(
            @RequestParam(value = "category", required = false) List<String> categories,
            @RequestParam(value = "brand", required = false) String brand,
            @RequestParam(value = "min_price", required = false) Double minPrice,
            @RequestParam(value = "max_price", required = false) Double maxPrice,
            @RequestParam(value = "min_stock", required = false) Integer minStock,
            @RequestParam(value = "max_stock", required = false) Integer maxStock,
            @RequestParam(value = "is_active", required = false) Boolean isActive,
            @RequestParam(value = "include_inactive", required = false) Boolean includeInactive,
            @RequestParam(value = "search", required = false) String search,
            @RequestParam(value = "skip", required = false, defaultValue = "0") int skip,
            @RequestParam(value = "limit", required = false, defaultValue = "100") int limit
    ) {
        Boolean effectiveIsActive = isActive;
        if (effectiveIsActive == null) {
            if (includeInactive != null && includeInactive) {
                effectiveIsActive = null;
            } else {
                effectiveIsActive = true;
            }
        }

        List<ProductCategory> categoryEnums = null;
        if (categories != null && !categories.isEmpty()) {
            categoryEnums = categories.stream().map(ProductCategory::fromValue).toList();
        }

        ProductListResponse response = productService.filterProducts(
                categoryEnums, brand, minPrice, maxPrice, minStock, maxStock, effectiveIsActive, search, skip, limit
        );
        return ResponseEntity.ok(response);
    }

    @GetMapping("/search/query")
    @Operation(summary = "Search products by query")
    public ResponseEntity<ProductListResponse> searchProducts(
            @RequestParam("q") String query,
            @RequestParam(value = "skip", required = false, defaultValue = "0") int skip,
            @RequestParam(value = "limit", required = false, defaultValue = "100") int limit
    ) {
        return ResponseEntity.ok(productService.filterProducts(
                null, null, null, null, null, null, true, query, skip, limit
        ));
    }

    @GetMapping("/category/{category}")
    @Operation(summary = "Get products by category")
    public ResponseEntity<ProductListResponse> getProductsByCategory(
            @PathVariable("category") String category,
            @RequestParam(value = "skip", required = false, defaultValue = "0") int skip,
            @RequestParam(value = "limit", required = false, defaultValue = "100") int limit
    ) {
        ProductCategory cat = ProductCategory.fromValue(category);
        List<ProductCategory> categories = cat != null ? List.of(cat) : null;
        return ResponseEntity.ok(productService.filterProducts(
                categories, null, null, null, null, null, true, null, skip, limit
        ));
    }

    @GetMapping({"/low-stock", "/alerts/low-stock"})
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @Operation(summary = "Get low stock alerts")
    public ResponseEntity<List<LowStockAlert>> getLowStock(
            @RequestParam(value = "threshold", required = false) Integer threshold
    ) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(productService.getLowStockAlerts(threshold, userId));
    }

    @GetMapping("/categories")
    @Operation(summary = "Get list of all product categories")
    public ResponseEntity<List<String>> getCategories() {
        List<String> list = Arrays.stream(ProductCategory.values()).map(ProductCategory::getValue).toList();
        return ResponseEntity.ok(list);
    }
}
