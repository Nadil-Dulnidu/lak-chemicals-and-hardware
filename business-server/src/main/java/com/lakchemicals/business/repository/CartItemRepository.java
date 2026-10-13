package com.lakchemicals.business.repository;

import com.lakchemicals.business.entity.CartItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface CartItemRepository extends JpaRepository<CartItem, Integer> {

    Optional<CartItem> findByCart_CartIdAndProduct_Id(Integer cartId, UUID productId);

    List<CartItem> findByCart_CartId(Integer cartId);

    void deleteByCart_CartId(Integer cartId);
}
