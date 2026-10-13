package com.lakchemicals.business.service;

import com.lakchemicals.business.constants.PaymentStatus;
import com.lakchemicals.business.dto.order.OrderResponse;
import com.lakchemicals.business.dto.payment.PaymentConfirmResponse;
import com.lakchemicals.business.dto.payment.PaymentSessionResponse;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.exception.ResourceNotFoundException;
import com.stripe.Stripe;
import com.stripe.exception.StripeException;
import com.stripe.model.checkout.Session;
import com.stripe.param.checkout.SessionCreateParams;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class PaymentService {

    private final OrderService orderService;

    @Value("${stripe.secret-key:}")
    private String stripeSecretKey;

    @Value("${stripe.frontend-url:http://localhost:3000}")
    private String frontendUrl;

    @PostConstruct
    public void init() {
        if (stripeSecretKey != null && !stripeSecretKey.isBlank()) {
            Stripe.apiKey = stripeSecretKey;
            log.info("Initialized Stripe SDK");
        } else {
            log.warn("Stripe secret key is not configured");
        }
    }

    public PaymentSessionResponse createCheckoutSession(Integer orderId) throws StripeException {
        OrderResponse order = orderService.getOrderByIdAdmin(orderId);
        if (order == null) {
            throw new ResourceNotFoundException("Order " + orderId + " not found");
        }

        List<SessionCreateParams.LineItem> lineItems = new ArrayList<>();
        if (order.getItems() != null && !order.getItems().isEmpty()) {
            for (var item : order.getItems()) {
                long unitAmountInCents = item.getUnitPrice().multiply(new java.math.BigDecimal(100)).longValue();
                String productName = item.getProductName() != null ? item.getProductName() : "Product " + item.getProductId();

                SessionCreateParams.LineItem lineItem = SessionCreateParams.LineItem.builder()
                        .setQuantity((long) item.getQuantity())
                        .setPriceData(
                                SessionCreateParams.LineItem.PriceData.builder()
                                        .setCurrency("lkr")
                                        .setUnitAmount(unitAmountInCents)
                                        .setProductData(
                                                SessionCreateParams.LineItem.PriceData.ProductData.builder()
                                                        .setName(productName)
                                                        .build()
                                        )
                                        .build()
                        )
                        .build();
                lineItems.add(lineItem);
            }
        } else {
            // Fallback for orders with no items snapshot
            long amountInCents = order.getTotalAmount().multiply(new java.math.BigDecimal(100)).longValue();
            lineItems.add(
                    SessionCreateParams.LineItem.builder()
                            .setQuantity(1L)
                            .setPriceData(
                                    SessionCreateParams.LineItem.PriceData.builder()
                                            .setCurrency("lkr")
                                            .setUnitAmount(amountInCents)
                                            .setProductData(
                                                    SessionCreateParams.LineItem.PriceData.ProductData.builder()
                                                            .setName("Order #" + orderId)
                                                            .build()
                                            )
                                            .build()
                            )
                            .build()
            );
        }

        Map<String, String> metadata = new HashMap<>();
        metadata.put("order_id", String.valueOf(orderId));

        SessionCreateParams params = SessionCreateParams.builder()
                .addPaymentMethodType(SessionCreateParams.PaymentMethodType.CARD)
                .setMode(SessionCreateParams.Mode.PAYMENT)
                .setSuccessUrl(frontendUrl + "/payment/success?order_id=" + orderId + "&session_id={CHECKOUT_SESSION_ID}")
                .setCancelUrl(frontendUrl + "/payment/cancel?order_id=" + orderId)
                .addAllLineItem(lineItems)
                .putAllMetadata(metadata)
                .build();

        Session session = Session.create(params);
        log.info("Stripe Checkout Session created for order {}: {}", orderId, session.getId());

        return PaymentSessionResponse.builder()
                .checkoutUrl(session.getUrl())
                .sessionId(session.getId())
                .build();
    }

    public PaymentConfirmResponse confirmPayment(Integer orderId, String sessionId) throws StripeException {
        Session session = Session.retrieve(sessionId);

        if (!"paid".equalsIgnoreCase(session.getPaymentStatus())) {
            throw new BadRequestException("Payment has not been completed");
        }

        String sessionOrderId = session.getMetadata().get("order_id");
        if (sessionOrderId == null || !sessionOrderId.equals(String.valueOf(orderId))) {
            throw new BadRequestException("Session does not match the provided order");
        }

        orderService.updatePaymentStatus(orderId, PaymentStatus.PAID);
        log.info("Payment confirmed for order {}, session {}", orderId, sessionId);

        return PaymentConfirmResponse.builder()
                .message("Payment confirmed")
                .orderId(orderId)
                .paymentStatus("PAID")
                .build();
    }
}
