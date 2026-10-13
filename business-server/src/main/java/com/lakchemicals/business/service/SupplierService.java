package com.lakchemicals.business.service;

import com.lakchemicals.business.dto.supplier.*;
import com.lakchemicals.business.entity.Product;
import com.lakchemicals.business.entity.Supplier;
import com.lakchemicals.business.entity.SupplierProduct;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.exception.ResourceNotFoundException;
import com.lakchemicals.business.repository.ProductRepository;
import com.lakchemicals.business.repository.SupplierProductRepository;
import com.lakchemicals.business.repository.SupplierRepository;
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

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class SupplierService {

    private final SupplierRepository supplierRepository;
    private final ProductRepository productRepository;
    private final SupplierProductRepository supplierProductRepository;

    @Transactional
    public SupplierResponse createSupplier(SupplierCreateRequest request, String userId) {
        log.info("Creating supplier: {} by user: {}", request.getName(), userId);

        if (supplierRepository.findByEmailIgnoreCase(request.getEmail()).isPresent()) {
            throw new BadRequestException("Supplier with email '" + request.getEmail() + "' already exists");
        }

        Supplier supplier = Supplier.builder()
                .name(request.getName())
                .contactPerson(request.getContactPerson())
                .contactNumber(request.getContactNumber())
                .email(request.getEmail().toLowerCase().trim())
                .address(request.getAddress())
                .isActive(true)
                .build();

        Supplier saved = supplierRepository.save(supplier);
        return mapToResponse(saved);
    }

    @Transactional(readOnly = true)
    public SupplierResponse getSupplierById(UUID id, String userId) {
        Supplier supplier = supplierRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Supplier not found with id: " + id));
        return mapToResponse(supplier);
    }

    @Transactional
    public SupplierResponse updateSupplier(UUID id, SupplierUpdateRequest request, String userId) {
        log.info("Updating supplier: {} by user: {}", id, userId);
        Supplier supplier = supplierRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Supplier not found with id: " + id));

        if (request.getName() != null) {
            supplier.setName(request.getName());
        }
        if (request.getContactPerson() != null) {
            supplier.setContactPerson(request.getContactPerson());
        }
        if (request.getContactNumber() != null) {
            supplier.setContactNumber(request.getContactNumber());
        }
        if (request.getEmail() != null) {
            String newEmail = request.getEmail().toLowerCase().trim();
            if (!newEmail.equalsIgnoreCase(supplier.getEmail()) && supplierRepository.findByEmailIgnoreCase(newEmail).isPresent()) {
                throw new BadRequestException("Supplier with email '" + newEmail + "' already exists");
            }
            supplier.setEmail(newEmail);
        }
        if (request.getAddress() != null) {
            supplier.setAddress(request.getAddress());
        }
        if (request.getIsActive() != null) {
            supplier.setIsActive(request.getIsActive());
        }

        Supplier saved = supplierRepository.save(supplier);
        return mapToResponse(saved);
    }

    @Transactional
    public void deleteSupplier(UUID id, String userId) {
        log.info("Soft-deleting supplier: {} by user: {}", id, userId);
        Supplier supplier = supplierRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Supplier not found with id: " + id));
        supplier.setIsActive(false);
        supplierRepository.save(supplier);
    }

    @Transactional(readOnly = true)
    public SupplierListResponse getAllSuppliers(int skip, int limit, boolean includeInactive, String userId) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "createdAt"));

        Page<Supplier> supplierPage;
        if (includeInactive) {
            supplierPage = supplierRepository.findAll(pageable);
        } else {
            supplierPage = supplierRepository.findByIsActiveTrue(pageable);
        }

        List<SupplierResponse> dtos = supplierPage.getContent().stream()
                .map(this::mapToResponse)
                .toList();

        return SupplierListResponse.builder()
                .suppliers(dtos)
                .total(supplierPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(supplierPage.hasNext())
                .build();
    }

    @Transactional(readOnly = true)
    public SupplierListResponse filterSuppliers(Boolean isActive, String search, int skip, int limit) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "createdAt"));

        Specification<Supplier> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (isActive != null) {
                predicates.add(cb.equal(root.get("isActive"), isActive));
            }
            if (search != null && !search.isBlank()) {
                String pattern = "%" + search.toLowerCase() + "%";
                Predicate nameMatch = cb.like(cb.lower(root.get("name")), pattern);
                Predicate emailMatch = cb.like(cb.lower(root.get("email")), pattern);
                Predicate contactMatch = cb.like(cb.lower(root.get("contactPerson")), pattern);
                predicates.add(cb.or(nameMatch, emailMatch, contactMatch));
            }

            return cb.and(predicates.toArray(new Predicate[0]));
        };

        Page<Supplier> supplierPage = supplierRepository.findAll(spec, pageable);

        List<SupplierResponse> dtos = supplierPage.getContent().stream()
                .map(this::mapToResponse)
                .toList();

        return SupplierListResponse.builder()
                .suppliers(dtos)
                .total(supplierPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(supplierPage.hasNext())
                .build();
    }

    @Transactional
    public SupplierProductResponse linkProduct(UUID supplierId, UUID productId, Double supplyPrice, String userId) {
        Supplier supplier = supplierRepository.findById(supplierId)
                .orElseThrow(() -> new ResourceNotFoundException("Supplier not found with id: " + supplierId));

        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + productId));

        SupplierProduct sp = supplierProductRepository.findBySupplierIdAndProductId(supplierId, productId)
                .orElse(SupplierProduct.builder()
                        .supplier(supplier)
                        .product(product)
                        .createdAt(LocalDateTime.now())
                        .build());

        if (supplyPrice != null) {
            sp.setSupplyPrice(supplyPrice);
        }

        SupplierProduct saved = supplierProductRepository.save(sp);

        return SupplierProductResponse.builder()
                .supplierId(supplier.getId())
                .productId(product.getId())
                .supplyPrice(saved.getSupplyPrice())
                .createdAt(saved.getCreatedAt())
                .lastSuppliedDate(saved.getLastSuppliedDate())
                .build();
    }

    @Transactional
    public void unlinkProduct(UUID supplierId, UUID productId, String userId) {
        supplierProductRepository.findBySupplierIdAndProductId(supplierId, productId)
                .ifPresent(supplierProductRepository::delete);
    }

    @Transactional(readOnly = true)
    public SupplierDetailResponse getSupplierDetails(UUID supplierId, String userId) {
        Supplier supplier = supplierRepository.findById(supplierId)
                .orElseThrow(() -> new ResourceNotFoundException("Supplier not found with id: " + supplierId));

        List<SupplierProduct> supplierProducts = supplierProductRepository.findBySupplierId(supplierId);
        List<ProductSupplierInfo> productInfos = supplierProducts.stream().map(sp ->
                ProductSupplierInfo.builder()
                        .productId(sp.getProduct().getId())
                        .productName(sp.getProduct().getName())
                        .supplyPrice(sp.getSupplyPrice())
                        .lastSuppliedDate(sp.getLastSuppliedDate())
                        .build()
        ).toList();

        SupplierDetailResponse response = SupplierDetailResponse.builder()
                .id(supplier.getId())
                .name(supplier.getName())
                .contactPerson(supplier.getContactPerson())
                .contactNumber(supplier.getContactNumber())
                .email(supplier.getEmail())
                .address(supplier.getAddress())
                .createdAt(supplier.getCreatedAt())
                .lastPurchaseDate(supplier.getLastPurchaseDate())
                .isActive(supplier.getIsActive())
                .products(productInfos)
                .build();

        return response;
    }

    public SupplierResponse mapToResponse(Supplier supplier) {
        return SupplierResponse.builder()
                .id(supplier.getId())
                .name(supplier.getName())
                .contactPerson(supplier.getContactPerson())
                .contactNumber(supplier.getContactNumber())
                .email(supplier.getEmail())
                .address(supplier.getAddress())
                .createdAt(supplier.getCreatedAt())
                .lastPurchaseDate(supplier.getLastPurchaseDate())
                .isActive(supplier.getIsActive())
                .build();
    }
}
