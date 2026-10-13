package com.lakchemicals.business.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletRequestWrapper;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * Filter to normalize request URIs by stripping trailing slashes.
 * In Spring Boot 3 / Spring MVC 6+, trailing slash matching is disabled by default,
 * causing requests like /products/ or /suppliers/ to fail with NoResourceFoundException.
 * This filter ensures all requests with trailing slashes transparently match their endpoints.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TrailingSlashFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        String uri = request.getRequestURI();
        if (uri != null && uri.length() > 1 && uri.endsWith("/")) {
            String trimmedUri = uri.replaceAll("/+$", "");
            HttpServletRequest wrappedRequest = new HttpServletRequestWrapper(request) {
                @Override
                public String getRequestURI() {
                    return trimmedUri;
                }

                @Override
                public String getServletPath() {
                    String servletPath = super.getServletPath();
                    if (servletPath != null && servletPath.length() > 1 && servletPath.endsWith("/")) {
                        return servletPath.replaceAll("/+$", "");
                    }
                    return servletPath;
                }
            };
            filterChain.doFilter(wrappedRequest, response);
        } else {
            filterChain.doFilter(request, response);
        }
    }
}
