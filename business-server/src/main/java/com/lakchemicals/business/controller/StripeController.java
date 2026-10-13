package com.lakchemicals.business.controller;

import com.lakchemicals.business.dto.payment.PaymentConfirmResponse;
import com.lakchemicals.business.dto.payment.PaymentSessionResponse;
import com.lakchemicals.business.service.PaymentService;
import com.stripe.exception.StripeException;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping({"/api/v1/payments", "/api/v1/stripe", "/payments", "/stripe"})
@Tag(name = "Payments", description = "Stripe Payment Endpoints")
@RequiredArgsConstructor
public class StripeController {

    private final PaymentService paymentService;

    @PostMapping("/create-payment-session/{order_id}")
    @Operation(summary = "Create a Stripe Checkout Session for an order")
    public ResponseEntity<PaymentSessionResponse> createPaymentSession(@PathVariable("order_id") Integer orderId) throws StripeException {
        return ResponseEntity.status(HttpStatus.CREATED).body(paymentService.createCheckoutSession(orderId));
    }

    @PostMapping("/confirm-payment/{order_id}")
    @Operation(summary = "Confirm Stripe payment for an order")
    public ResponseEntity<PaymentConfirmResponse> confirmPayment(
            @PathVariable("order_id") Integer orderId,
            @RequestParam("session_id") String sessionId
    ) throws StripeException {
        return ResponseEntity.ok(paymentService.confirmPayment(orderId, sessionId));
    }
}
