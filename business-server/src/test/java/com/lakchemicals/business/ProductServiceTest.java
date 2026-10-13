package com.lakchemicals.business;

import com.lakchemicals.business.constants.ProductCategory;
import com.lakchemicals.business.dto.product.*;
import com.lakchemicals.business.entity.Product;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.exception.ResourceNotFoundException;
import com.lakchemicals.business.repository.ProductRepository;
import com.lakchemicals.business.service.ProductService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ProductServiceTest {

    @Mock
    private ProductRepository productRepository;

    @InjectMocks
    private ProductService productService;

    private Product product;
    private UUID productId;

    @BeforeEach
    void setUp() {
        productId = UUID.randomUUID();
        product = Product.builder()
                .id(productId)
                .name("PVC Solvent Cement")
                .description("High quality cement")
                .brand("LakChem")
                .category(ProductCategory.CHEMICALS)
                .price(450.0)
                .stockQty(25)
                .reorderLevel(10)
                .imageUrl("https://example.com/pvc.jpg")
                .createdAt(LocalDateTime.now())
                .isActive(true)
                .build();
    }

    @Test
    void testCreateProduct_Success() {
        ProductCreateRequest request = ProductCreateRequest.builder()
                .name("PVC Solvent Cement")
                .price(450.0)
                .stockQty(25)
                .category(ProductCategory.CHEMICALS)
                .build();

        when(productRepository.findByNameIgnoreCase("PVC Solvent Cement")).thenReturn(Optional.empty());
        when(productRepository.save(any(Product.class))).thenReturn(product);

        ProductResponse response = productService.createProduct(request, "admin");

        assertNotNull(response);
        assertEquals("PVC Solvent Cement", response.getName());
        assertEquals(450.0, response.getPrice());
        assertEquals(25, response.getStockQty());
        verify(productRepository, times(1)).save(any(Product.class));
    }

    @Test
    void testCreateProduct_DuplicateName_ThrowsBadRequest() {
        ProductCreateRequest request = ProductCreateRequest.builder()
                .name("PVC Solvent Cement")
                .price(450.0)
                .stockQty(25)
                .build();

        when(productRepository.findByNameIgnoreCase("PVC Solvent Cement")).thenReturn(Optional.of(product));

        assertThrows(BadRequestException.class, () -> productService.createProduct(request, "admin"));
        verify(productRepository, never()).save(any(Product.class));
    }

    @Test
    void testGetProductById_Success() {
        when(productRepository.findById(productId)).thenReturn(Optional.of(product));

        ProductResponse response = productService.getProductById(productId, "user");

        assertNotNull(response);
        assertEquals(productId, response.getId());
        assertEquals("PVC Solvent Cement", response.getName());
    }

    @Test
    void testGetProductById_NotFound_ThrowsResourceNotFound() {
        when(productRepository.findById(productId)).thenReturn(Optional.empty());

        assertThrows(ResourceNotFoundException.class, () -> productService.getProductById(productId, "user"));
    }

    @Test
    void testUpdateProduct_Success() {
        ProductUpdateRequest request = ProductUpdateRequest.builder()
                .name("Updated PVC Cement")
                .price(500.0)
                .build();

        when(productRepository.findById(productId)).thenReturn(Optional.of(product));
        when(productRepository.save(any(Product.class))).thenAnswer(invocation -> invocation.getArgument(0));

        ProductResponse response = productService.updateProduct(productId, request, "admin");

        assertNotNull(response);
        assertEquals("Updated PVC Cement", response.getName());
        assertEquals(500.0, response.getPrice());
    }

    @Test
    void testDeleteProduct_SoftDelete() {
        when(productRepository.findById(productId)).thenReturn(Optional.of(product));
        when(productRepository.save(any(Product.class))).thenAnswer(invocation -> invocation.getArgument(0));

        productService.deleteProduct(productId, "admin");

        assertFalse(product.getIsActive());
        verify(productRepository, times(1)).save(product);
    }

    @Test
    void testGetAllProducts_Success() {
        Page<Product> page = new PageImpl<>(List.of(product));
        when(productRepository.findByIsActiveTrue(any(Pageable.class))).thenReturn(page);

        ProductListResponse response = productService.getAllProducts(0, 10, false, "user");

        assertNotNull(response);
        assertEquals(1, response.getProducts().size());
        assertEquals(1L, response.getTotal());
    }

    @Test
    void testGetLowStockAlerts() {
        Product lowStockProduct = Product.builder()
                .id(UUID.randomUUID())
                .name("Low Stock Paint")
                .price(1200.0)
                .stockQty(3)
                .reorderLevel(10)
                .isActive(true)
                .build();

        when(productRepository.findLowStockProducts()).thenReturn(List.of(lowStockProduct));

        List<LowStockAlert> alerts = productService.getLowStockAlerts(null, "admin");

        assertEquals(1, alerts.size());
        assertEquals(7, alerts.get(0).getRestockNeeded());
        assertEquals("medium", alerts.get(0).getPriority());
    }

    @Test
    void testUpdateStock_Success() {
        when(productRepository.findById(productId)).thenReturn(Optional.of(product));
        when(productRepository.save(any(Product.class))).thenAnswer(invocation -> invocation.getArgument(0));

        ProductResponse response = productService.updateStock(productId, 10, "admin");

        assertEquals(35, response.getStockQty());
    }

    @Test
    void testUpdateStock_InsufficientStock_ThrowsBadRequest() {
        when(productRepository.findById(productId)).thenReturn(Optional.of(product));

        assertThrows(BadRequestException.class, () -> productService.updateStock(productId, -50, "admin"));
    }
}
