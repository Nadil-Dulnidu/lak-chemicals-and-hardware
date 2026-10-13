package com.lakchemicals.business.repository;

import com.lakchemicals.business.entity.OrderProduct;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface OrderProductRepository extends JpaRepository<OrderProduct, Integer> {

    List<OrderProduct> findByOrder_OrderId(Integer orderId);

    List<OrderProduct> findByProduct_Id(UUID productId);
}
