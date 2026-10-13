package com.lakchemicals.business.service;

import com.lakchemicals.business.constants.ProductCategory;
import com.lakchemicals.business.dto.product.*;
import com.lakchemicals.business.entity.Product;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.exception.ResourceNotFoundException;
import com.lakchemicals.business.repository.ProductRepository;
import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;

    @Transactional
    public ProductResponse createProduct(ProductCreateRequest request, String userId) {
        log.info("Creating product: {} by user: {}", request.getName(), userId);

        if (productRepository.findByNameIgnoreCase(request.getName()).isPresent()) {
            throw new BadRequestException("Product with name '" + request.getName() + "' already exists");
        }

        Product product = Product.builder()
                .name(request.getName())
                .description(request.getDescription())
                .brand(request.getBrand())
                .category(request.getCategory())
                .price(request.getPrice())
                .stockQty(request.getStockQty() != null ? request.getStockQty() : 0)
                .reorderLevel(request.getReorderLevel() != null ? request.getReorderLevel() : 10)
                .imageUrl(request.getImageUrl())
                .isActive(true)
                .build();

        Product saved = productRepository.save(product);
        return mapToResponse(saved);
    }

    @Transactional(readOnly = true)
    public ProductResponse getProductById(UUID id, String userId) {
        log.debug("Fetching product: {} by user: {}", id, userId);
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));
        return mapToResponse(product);
    }

    @Transactional
    public ProductResponse updateProduct(UUID id, ProductUpdateRequest request, String userId) {
        log.info("Updating product: {} by user: {}", id, userId);
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));

        if (request.getName() != null) {
            product.setName(request.getName());
        }
        if (request.getDescription() != null) {
            product.setDescription(request.getDescription());
        }
        if (request.getBrand() != null) {
            product.setBrand(request.getBrand());
        }
        if (request.getCategory() != null) {
            product.setCategory(request.getCategory());
        }
        if (request.getPrice() != null) {
            product.setPrice(request.getPrice());
        }
        if (request.getStockQty() != null) {
            product.setStockQty(request.getStockQty());
        }
        if (request.getReorderLevel() != null) {
            product.setReorderLevel(request.getReorderLevel());
        }
        if (request.getImageUrl() != null) {
            product.setImageUrl(request.getImageUrl());
        }
        if (request.getIsActive() != null) {
            product.setIsActive(request.getIsActive());
        }

        Product saved = productRepository.save(product);
        return mapToResponse(saved);
    }

    @Transactional
    public void deleteProduct(UUID id, String userId) {
        log.info("Soft-deleting product: {} by user: {}", id, userId);
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));
        product.setIsActive(false);
        productRepository.save(product);
    }

    @Transactional(readOnly = true)
    public ProductListResponse getAllProducts(int skip, int limit, boolean includeInactive, String userId) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "createdAt"));

        Page<Product> productPage;
        if (includeInactive) {
            productPage = productRepository.findAll(pageable);
        } else {
            productPage = productRepository.findByIsActiveTrue(pageable);
        }

        List<ProductResponse> dtos = productPage.getContent().stream()
                .map(this::mapToResponse)
                .toList();

        return ProductListResponse.builder()
                .products(dtos)
                .total(productPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(productPage.hasNext())
                .build();
    }

    @Transactional(readOnly = true)
    public ProductListResponse filterProducts(
            List<ProductCategory> categories,
            String brand,
            Double minPrice,
            Double maxPrice,
            Integer minStock,
            Integer maxStock,
            Boolean isActive,
            String search,
            int skip,
            int limit
    ) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "createdAt"));

        Specification<Product> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (isActive != null) {
                predicates.add(cb.equal(root.get("isActive"), isActive));
            }
            if (categories != null && !categories.isEmpty()) {
                predicates.add(root.get("category").in(categories));
            }
            if (brand != null && !brand.isBlank()) {
                predicates.add(cb.equal(cb.lower(root.get("brand")), brand.toLowerCase()));
            }
            if (minPrice != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("price"), minPrice));
            }
            if (maxPrice != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("price"), maxPrice));
            }
            if (minStock != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("stockQty"), minStock));
            }
            if (maxStock != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("stockQty"), maxStock));
            }
            if (search != null && !search.isBlank()) {
                String pattern = "%" + search.toLowerCase() + "%";
                Predicate nameMatch = cb.like(cb.lower(root.get("name")), pattern);
                Predicate descMatch = cb.like(cb.lower(root.get("description")), pattern);
                predicates.add(cb.or(nameMatch, descMatch));
            }

            return cb.and(predicates.toArray(new Predicate[0]));
        };

        Page<Product> productPage = productRepository.findAll(spec, pageable);

        List<ProductResponse> dtos = productPage.getContent().stream()
                .map(this::mapToResponse)
                .toList();

        return ProductListResponse.builder()
                .products(dtos)
                .total(productPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(productPage.hasNext())
                .build();
    }

    @Transactional(readOnly = true)
    public List<LowStockAlert> getLowStockAlerts(Integer threshold, String userId) {
        List<Product> products = threshold != null ?
                productRepository.findLowStockProductsWithThreshold(threshold) :
                productRepository.findLowStockProducts();

        return products.stream().map(p -> {
            int target = threshold != null ? threshold : p.getReorderLevel();
            int needed = Math.max(0, target - p.getStockQty());
            String priority = p.getStockQty() == 0 ? "high" :
                    (p.getStockQty() <= p.getReorderLevel() / 2 ? "medium" : "low");

            return LowStockAlert.builder()
                    .id(p.getId())
                    .name(p.getName())
                    .description(p.getDescription())
                    .brand(p.getBrand())
                    .category(p.getCategory())
                    .price(p.getPrice())
                    .stockQty(p.getStockQty())
                    .reorderLevel(p.getReorderLevel())
                    .imageUrl(p.getImageUrl())
                    .createdAt(p.getCreatedAt())
                    .isActive(p.getIsActive())
                    .restockNeeded(needed)
                    .priority(priority)
                    .build();
        }).toList();
    }

    @Transactional
    public ProductResponse updateStock(UUID id, int quantityChange, String userId) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));

        int newStock = product.getStockQty() + quantityChange;
        if (newStock < 0) {
            throw new BadRequestException("Insufficient stock. Current: " + product.getStockQty() + ", Requested change: " + quantityChange);
        }

        product.setStockQty(newStock);
        return mapToResponse(productRepository.save(product));
    }

    public ProductResponse mapToResponse(Product product) {
        return ProductResponse.builder()
                .id(product.getId())
                .name(product.getName())
                .description(product.getDescription())
                .brand(product.getBrand())
                .category(product.getCategory())
                .price(product.getPrice())
                .stockQty(product.getStockQty())
                .reorderLevel(product.getReorderLevel())
                .imageUrl(product.getImageUrl())
                .createdAt(product.getCreatedAt())
                .isActive(product.getIsActive())
                .build();
    }
}
