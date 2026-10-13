package com.lakchemicals.business;

import com.lakchemicals.business.constants.QuotationStatus;
import com.lakchemicals.business.dto.quotation.*;
import com.lakchemicals.business.entity.*;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.repository.*;
import com.lakchemicals.business.service.EmailService;
import com.lakchemicals.business.service.QuotationService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class QuotationServiceTest {

    @Mock
    private QuotationRepository quotationRepository;

    @Mock
    private QuotationItemRepository quotationItemRepository;

    @Mock
    private CartRepository cartRepository;

    @Mock
    private CartItemRepository cartItemRepository;

    @Mock
    private ProductRepository productRepository;

    @Mock
    private EmailService emailService;

    @InjectMocks
    private QuotationService quotationService;

    private String userId = "user_789";
    private String userEmail = "customer@example.com";
    private Product product;

    @BeforeEach
    void setUp() {
        product = Product.builder()
                .id(UUID.randomUUID())
                .name("Steel Bar")
                .price(2500.0)
                .stockQty(100)
                .isActive(true)
                .build();
    }

    @Test
    void testCreateQuotation_Success() {
        QuotationItemRequest itemReq = QuotationItemRequest.builder()
                .productId(product.getId())
                .quantity(4)
                .build();

        QuotationCreateRequest request = QuotationCreateRequest.builder()
                .items(List.of(itemReq))
                .notes("Need by next week")
                .build();

        when(productRepository.findById(product.getId())).thenReturn(Optional.of(product));

        Quotation savedQuotation = Quotation.builder()
                .quotationId(10)
                .userId(userId)
                .userEmail(userEmail)
                .status(QuotationStatus.PENDING)
                .totalAmount(BigDecimal.ZERO)
                .createdAt(LocalDateTime.now())
                .quotationItems(new ArrayList<>())
                .build();

        when(quotationRepository.save(any(Quotation.class))).thenReturn(savedQuotation);
        when(quotationItemRepository.save(any(QuotationItem.class))).thenAnswer(invocation -> invocation.getArgument(0));

        QuotationResponse response = quotationService.createQuotation(userId, userEmail, request);

        assertNotNull(response);
        assertEquals(10, response.getQuotationId());
        assertEquals(QuotationStatus.PENDING, response.getStatus());
        verify(quotationItemRepository, times(1)).save(any(QuotationItem.class));
    }

    @Test
    void testCreateQuotation_EmptyItems_ThrowsBadRequest() {
        QuotationCreateRequest request = QuotationCreateRequest.builder()
                .items(List.of())
                .build();

        assertThrows(BadRequestException.class, () -> quotationService.createQuotation(userId, userEmail, request));
    }

    @Test
    void testUpdateQuotationStatus_Approved_DispatchesEmail() {
        Quotation quotation = Quotation.builder()
                .quotationId(10)
                .userId(userId)
                .userEmail(userEmail)
                .status(QuotationStatus.PENDING)
                .totalAmount(BigDecimal.valueOf(10000))
                .discountAmount(BigDecimal.ZERO)
                .quotationItems(new ArrayList<>())
                .build();

        when(quotationRepository.findById(10)).thenReturn(Optional.of(quotation));
        when(quotationRepository.save(any(Quotation.class))).thenAnswer(invocation -> invocation.getArgument(0));

        QuotationResponse response = quotationService.updateQuotationStatus(10, QuotationStatus.APPROVED, BigDecimal.valueOf(500));

        assertNotNull(response);
        assertEquals(QuotationStatus.APPROVED, response.getStatus());
        assertEquals(BigDecimal.valueOf(500), response.getDiscountAmount());
        verify(emailService, times(1)).sendQuotationStatusEmail(
                eq(userEmail), eq(10), eq(QuotationStatus.APPROVED), eq(BigDecimal.valueOf(10000)), eq(BigDecimal.valueOf(500))
        );
    }
}
