package com.lakchemicals.business.config;

import com.lakchemicals.business.security.ApiKeyAuthenticationFilter;
import com.lakchemicals.business.security.ClerkJwtAuthenticationFilter;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.List;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final ClerkJwtAuthenticationFilter clerkJwtAuthenticationFilter;
    private final ApiKeyAuthenticationFilter apiKeyAuthenticationFilter;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        // Public Root & Health endpoints
                        .requestMatchers("/", "/health", "/api/v1", "/api/v1/health").permitAll()
                        .requestMatchers("/actuator/**").permitAll()
                        .requestMatchers("/swagger-ui/**", "/swagger-ui.html", "/v3/api-docs/**").permitAll()

                        // Public Product Browsing
                        .requestMatchers(HttpMethod.GET, "/api/v1/products/**", "/products/**", "/api/v1/products", "/products").permitAll()

                        // Agent tools endpoints (can be accessed via API Key or Admin)
                        .requestMatchers("/api/v1/tools/**", "/tools/**", "/api/v1/agents/**", "/agents/**")
                        .hasAnyAuthority("ROLE_AGENT", "ROLE_ADMIN")

                        // Admin-only endpoints
                        .requestMatchers(HttpMethod.POST, "/api/v1/products/**", "/products/**").hasAuthority("ROLE_ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/v1/products/**", "/products/**").hasAuthority("ROLE_ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/v1/products/**", "/products/**").hasAuthority("ROLE_ADMIN")
                        .requestMatchers("/api/v1/suppliers/**", "/suppliers/**").hasAuthority("ROLE_ADMIN")
                        .requestMatchers("/api/v1/inventory/**", "/inventory/**").hasAuthority("ROLE_ADMIN")
                        .requestMatchers("/api/v1/reports/**", "/reports/**").hasAuthority("ROLE_ADMIN")

                        // Authenticated customer/user endpoints
                        .requestMatchers("/api/v1/cart/**", "/cart/**").authenticated()
                        .requestMatchers("/api/v1/orders/**", "/orders/**").authenticated()
                        .requestMatchers("/api/v1/quotations/**", "/quotations/**").authenticated()
                        .requestMatchers("/api/v1/payments/**", "/payments/**", "/api/v1/stripe/**", "/stripe/**").authenticated()

                        // Any other request must be authenticated
                        .anyRequest().authenticated()
                )
                .addFilterBefore(apiKeyAuthenticationFilter, UsernamePasswordAuthenticationFilter.class)
                .addFilterBefore(clerkJwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOriginPatterns(List.of(
                "http://localhost:*",
                "http://127.0.0.1:*",
                "https://*.vercel.app",
                "https://lakchemicalsandhardware.vercel.app"
        ));
        configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("*"));
        configuration.setAllowCredentials(true);
        configuration.setExposedHeaders(List.of("Authorization", "Content-Disposition", "x-api-key"));

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
