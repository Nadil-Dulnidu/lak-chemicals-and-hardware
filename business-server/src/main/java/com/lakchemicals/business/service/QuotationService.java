package com.lakchemicals.business.service;

import com.lakchemicals.business.constants.QuotationStatus;
import com.lakchemicals.business.dto.quotation.*;
import com.lakchemicals.business.entity.*;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.exception.ForbiddenException;
import com.lakchemicals.business.exception.ResourceNotFoundException;
import com.lakchemicals.business.repository.*;
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

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class QuotationService {

    private final QuotationRepository quotationRepository;
    private final QuotationItemRepository quotationItemRepository;
    private final CartRepository cartRepository;
    private final CartItemRepository cartItemRepository;
    private final ProductRepository productRepository;
    private final EmailService emailService;

    @Transactional
    public QuotationResponse createQuotation(String userId, String userEmail, QuotationCreateRequest request) {
        log.info("Creating quotation for user: {}", userId);

        if (request.getItems() == null || request.getItems().isEmpty()) {
            throw new BadRequestException("Quotation must contain at least one item");
        }

        Quotation quotation = Quotation.builder()
                .userId(userId)
                .userEmail(userEmail != null ? userEmail : userId + "@customer.lakchemicals.com")
                .status(QuotationStatus.PENDING)
                .totalAmount(BigDecimal.ZERO)
                .discountAmount(BigDecimal.ZERO)
                .notes(request.getNotes())
                .createdAt(LocalDateTime.now())
                .build();

        Quotation savedQuotation = quotationRepository.save(quotation);

        BigDecimal total = BigDecimal.ZERO;
        List<QuotationItem> items = new ArrayList<>();

        for (QuotationItemRequest itemReq : request.getItems()) {
            Product product = productRepository.findById(itemReq.getProductId())
                    .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + itemReq.getProductId()));

            BigDecimal unitPrice = BigDecimal.valueOf(product.getPrice());
            BigDecimal subtotal = unitPrice.multiply(BigDecimal.valueOf(itemReq.getQuantity()));
            total = total.add(subtotal);

            QuotationItem qi = QuotationItem.builder()
                    .quotation(savedQuotation)
                    .product(product)
                    .quantity(itemReq.getQuantity())
                    .unitPrice(unitPrice)
                    .subtotal(subtotal)
                    .build();

            items.add(quotationItemRepository.save(qi));
        }

        savedQuotation.setTotalAmount(total);
        savedQuotation.setQuotationItems(items);
        quotationRepository.save(savedQuotation);

        return mapToResponse(savedQuotation);
    }

    @Transactional
    public QuotationResponse createQuotationFromCart(String userId, String userEmail, QuotationFromCartRequest request) {
        log.info("Creating quotation from cart for user: {}", userId);

        Cart cart = cartRepository.findByUserId(userId)
                .orElseThrow(() -> new ResourceNotFoundException("Cart not found for user: " + userId));

        List<CartItem> cartItems = cartItemRepository.findByCart_CartId(cart.getCartId());
        if (cartItems.isEmpty()) {
            throw new BadRequestException("Cart is empty");
        }

        Quotation quotation = Quotation.builder()
                .userId(userId)
                .userEmail(userEmail != null ? userEmail : userId + "@customer.lakchemicals.com")
                .status(QuotationStatus.PENDING)
                .totalAmount(BigDecimal.ZERO)
                .discountAmount(BigDecimal.ZERO)
                .notes(request != null ? request.getNotes() : null)
                .createdAt(LocalDateTime.now())
                .build();

        Quotation savedQuotation = quotationRepository.save(quotation);

        BigDecimal total = BigDecimal.ZERO;
        List<QuotationItem> items = new ArrayList<>();

        for (CartItem ci : cartItems) {
            Product product = ci.getProduct();
            BigDecimal unitPrice = BigDecimal.valueOf(product.getPrice());
            BigDecimal subtotal = unitPrice.multiply(BigDecimal.valueOf(ci.getQuantity()));
            total = total.add(subtotal);

            QuotationItem qi = QuotationItem.builder()
                    .quotation(savedQuotation)
                    .product(product)
                    .quantity(ci.getQuantity())
                    .unitPrice(unitPrice)
                    .subtotal(subtotal)
                    .build();

            items.add(quotationItemRepository.save(qi));
        }

        savedQuotation.setTotalAmount(total);
        savedQuotation.setQuotationItems(items);
        quotationRepository.save(savedQuotation);

        // Clear cart
        cartItemRepository.deleteByCart_CartId(cart.getCartId());
        cart.getCartItems().clear();

        return mapToResponse(savedQuotation);
    }

    @Transactional(readOnly = true)
    public QuotationResponse getQuotationById(Integer quotationId, String userId, boolean isAdmin) {
        Quotation quotation = quotationRepository.findById(quotationId)
                .orElseThrow(() -> new ResourceNotFoundException("Quotation not found with id: " + quotationId));

        if (!isAdmin && !quotation.getUserId().equals(userId)) {
            throw new ForbiddenException("Access denied to quotation: " + quotationId);
        }

        return mapToResponse(quotation);
    }

    @Transactional(readOnly = true)
    public QuotationListResponse getUserQuotations(String userId, int skip, int limit) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "createdAt"));

        Page<Quotation> qPage = quotationRepository.findByUserId(userId, pageable);
        List<QuotationResponse> dtos = qPage.getContent().stream().map(this::mapToResponse).toList();

        return QuotationListResponse.builder()
                .quotations(dtos)
                .total(qPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(qPage.hasNext())
                .build();
    }

    @Transactional(readOnly = true)
    public QuotationListResponse filterQuotations(
            QuotationStatus status,
            LocalDateTime startDate,
            LocalDateTime endDate,
            int skip,
            int limit
    ) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "createdAt"));

        Specification<Quotation> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (status != null) {
                predicates.add(cb.equal(root.get("status"), status));
            }
            if (startDate != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("createdAt"), startDate));
            }
            if (endDate != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("createdAt"), endDate));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };

        Page<Quotation> qPage = quotationRepository.findAll(spec, pageable);
        List<QuotationResponse> dtos = qPage.getContent().stream().map(this::mapToResponse).toList();

        return QuotationListResponse.builder()
                .quotations(dtos)
                .total(qPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(qPage.hasNext())
                .build();
    }

    @Transactional
    public QuotationResponse updateQuotationStatus(Integer quotationId, QuotationStatus status, BigDecimal discountAmount) {
        Quotation quotation = quotationRepository.findById(quotationId)
                .orElseThrow(() -> new ResourceNotFoundException("Quotation not found with id: " + quotationId));

        quotation.setStatus(status);
        if (discountAmount != null) {
            quotation.setDiscountAmount(discountAmount);
        }

        Quotation saved = quotationRepository.save(quotation);

        // Send notification email asynchronously
        emailService.sendQuotationStatusEmail(
                saved.getUserEmail(),
                saved.getQuotationId(),
                saved.getStatus(),
                saved.getTotalAmount(),
                saved.getDiscountAmount()
        );

        return mapToResponse(saved);
    }

    @Transactional
    public void deleteQuotation(Integer quotationId, String userId, boolean isAdmin) {
        Quotation quotation = quotationRepository.findById(quotationId)
                .orElseThrow(() -> new ResourceNotFoundException("Quotation not found with id: " + quotationId));

        if (!isAdmin && !quotation.getUserId().equals(userId)) {
            throw new ForbiddenException("Access denied to delete quotation: " + quotationId);
        }

        quotationRepository.delete(quotation);
    }

    public QuotationResponse mapToResponse(Quotation q) {
        List<QuotationItemResponse> items = q.getQuotationItems() != null ?
                q.getQuotationItems().stream()
                        .filter(java.util.Objects::nonNull)
                        .map(qi -> QuotationItemResponse.builder()
                                .quotationItemId(qi.getQuotationItemId())
                                .productId(qi.getProduct() != null ? qi.getProduct().getId() : null)
                                .productName(qi.getProduct() != null ? qi.getProduct().getName() : null)
                                .quantity(qi.getQuantity())
                                .unitPrice(qi.getUnitPrice())
                                .subtotal(qi.getSubtotal())
                                .build()
                        ).toList() : new ArrayList<>();

        return QuotationResponse.builder()
                .quotationId(q.getQuotationId())
                .userId(q.getUserId())
                .status(q.getStatus())
                .totalAmount(q.getTotalAmount())
                .discountAmount(q.getDiscountAmount() != null ? q.getDiscountAmount() : BigDecimal.ZERO)
                .createdAt(q.getCreatedAt())
                .updatedAt(q.getUpdatedAt())
                .notes(q.getNotes())
                .items(items)
                .build();
    }
}
