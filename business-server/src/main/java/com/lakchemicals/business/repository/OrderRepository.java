package com.lakchemicals.business.repository;

import com.lakchemicals.business.constants.OrderStatus;
import com.lakchemicals.business.constants.PaymentStatus;
import com.lakchemicals.business.entity.Order;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface OrderRepository extends JpaRepository<Order, Integer>, JpaSpecificationExecutor<Order> {

    List<Order> findByUserIdOrderByOrderDateDesc(String userId);

    Page<Order> findByUserId(String userId, Pageable pageable);

    List<Order> findByStatus(OrderStatus status);

    List<Order> findByPaymentStatus(PaymentStatus paymentStatus);

    List<Order> findByOrderDateBetweenOrderByOrderDateDesc(LocalDateTime start, LocalDateTime end);
}
