package com.lakchemicals.business.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

@Slf4j
@Component
public class ApiKeyAuthenticationFilter extends OncePerRequestFilter {

    @Value("${app.api-key:}")
    private String configuredApiKey;

    @Value("${app.api-key-header:x-api-key}")
    private String apiKeyHeaderName;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        String requestApiKey = request.getHeader(apiKeyHeaderName);

        if (requestApiKey != null && requestApiKey.equals(configuredApiKey)) {
            UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(
                            "service-account",
                            requestApiKey,
                            List.of(
                                    new SimpleGrantedAuthority("ROLE_AGENT"),
                                    new SimpleGrantedAuthority("ROLE_ADMIN"),
                                    new SimpleGrantedAuthority("ROLE_SERVICE")
                            )
                    );
            SecurityContextHolder.getContext().setAuthentication(authentication);
            log.debug("Authenticated via API Key");
        }

        filterChain.doFilter(request, response);
    }
}
