package com.lakchemicals.business.service;

import com.lakchemicals.business.constants.QuotationStatus;
import jakarta.mail.internet.MimeMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;

@Slf4j
@Service
public class EmailService {

    @Autowired(required = false)
    private JavaMailSender mailSender;

    @Value("${spring.mail.username:}")
    private String senderEmail;

    @Async
    public void sendQuotationStatusEmail(
            String recipientEmail,
            Integer quotationId,
            QuotationStatus status,
            BigDecimal totalAmount,
            BigDecimal discountAmount
    ) {
        if (mailSender == null || recipientEmail == null || recipientEmail.isBlank()) {
            log.info("Email sender not configured or recipient empty. Skipping email to {}", recipientEmail);
            return;
        }

        try {
            if (status == QuotationStatus.APPROVED) {
                String subject = "Your Quotation #" + quotationId + " Has Been Approved – LAK Chemicals & Hardware";
                String htmlBody = buildApprovedHtml(quotationId, totalAmount, discountAmount);
                sendHtmlEmail(recipientEmail, subject, htmlBody);
            } else if (status == QuotationStatus.REJECTED) {
                String subject = "Update on Your Quotation #" + quotationId + " – LAK Chemicals & Hardware";
                String htmlBody = buildRejectedHtml(quotationId);
                sendHtmlEmail(recipientEmail, subject, htmlBody);
            }
        } catch (Exception e) {
            log.error("Failed to send quotation status email: {}", e.getMessage(), e);
        }
    }

    private void sendHtmlEmail(String recipientEmail, String subject, String htmlBody) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setFrom(senderEmail);
            helper.setTo(recipientEmail);
            helper.setSubject(subject);
            helper.setText(htmlBody, true);
            mailSender.send(message);
            log.info("Email sent successfully to {}", recipientEmail);
        } catch (Exception e) {
            log.error("Error sending email to {}: {}", recipientEmail, e.getMessage());
        }
    }

    private String buildApprovedHtml(Integer quotationId, BigDecimal totalAmount, BigDecimal discountAmount) {
        BigDecimal discount = discountAmount != null ? discountAmount : BigDecimal.ZERO;
        BigDecimal total = totalAmount != null ? totalAmount : BigDecimal.ZERO;
        BigDecimal net = total.subtract(discount);

        String discountRow = discount.compareTo(BigDecimal.ZERO) > 0 ?
                "<tr><td style=\"padding:8px 0;color:#555;font-size:14px;\">Discount Applied</td>" +
                "<td style=\"padding:8px 0;color:#e53e3e;font-size:14px;text-align:right;\">- Rs." +
                discount + "</td></tr>" : "";

        return "<!DOCTYPE html><html><body style=\"font-family:Arial,sans-serif;background:#f7f8fa;margin:0;padding:0;\">" +
                "<div style=\"max-width:560px;margin:40px auto;background:#fff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden;\">" +
                "<div style=\"background:linear-gradient(135deg,#38a169,#276749);padding:32px 40px;\">" +
                "<h1 style=\"color:#fff;margin:0;font-size:24px;\">✅ Quotation Approved</h1></div>" +
                "<div style=\"padding:32px 40px;\">" +
                "<p style=\"color:#333;font-size:16px;margin-top:0;\">Great news! Your quotation request <strong>#" + quotationId + "</strong> has been <strong style=\"color:#38a169;\">approved</strong>.</p>" +
                "<table style=\"width:100%;border-top:1px solid #e2e8f0;margin:24px 0;\">" +
                "<tr><td style=\"padding:12px 0;color:#555;font-size:14px;\">Quotation ID</td><td style=\"padding:12px 0;color:#333;font-size:14px;text-align:right;\">#" + quotationId + "</td></tr>" +
                "<tr><td style=\"padding:8px 0;color:#555;font-size:14px;\">Original Amount</td><td style=\"padding:8px 0;color:#333;font-size:14px;text-align:right;\">Rs." + total + "</td></tr>" +
                discountRow +
                "<tr style=\"border-top:1px solid #e2e8f0;\"><td style=\"padding:12px 0;color:#333;font-weight:bold;font-size:15px;\">Net Amount</td>" +
                "<td style=\"padding:12px 0;color:#38a169;font-weight:bold;font-size:15px;text-align:right;\">Rs." + net + "</td></tr></table>" +
                "<p style=\"color:#555;font-size:14px;\">You can now proceed to place your order using this quotation. Please log in to your account to continue.</p></div>" +
                "<div style=\"background:#f7f8fa;padding:18px 40px;text-align:center;\">" +
                "<p style=\"color:#aaa;font-size:12px;margin:0;\">LAK Chemicals &amp; Hardware &nbsp;|&nbsp; This is an automated message.</p></div></div></body></html>";
    }

    private String buildRejectedHtml(Integer quotationId) {
        return "<!DOCTYPE html><html><body style=\"font-family:Arial,sans-serif;background:#f7f8fa;margin:0;padding:0;\">" +
                "<div style=\"max-width:560px;margin:40px auto;background:#fff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden;\">" +
                "<div style=\"background:linear-gradient(135deg,#e53e3e,#9b2c2c);padding:32px 40px;\">" +
                "<h1 style=\"color:#fff;margin:0;font-size:24px;\">❌ Quotation Rejected</h1></div>" +
                "<div style=\"padding:32px 40px;\">" +
                "<p style=\"color:#333;font-size:16px;margin-top:0;\">We regret to inform you that your quotation request <strong>#" + quotationId + "</strong> has been <strong style=\"color:#e53e3e;\">rejected</strong>.</p>" +
                "<p style=\"color:#555;font-size:14px;\">This may be due to stock availability or pricing constraints. Please feel free to submit a new quotation request or contact us for more information.</p></div>" +
                "<div style=\"background:#f7f8fa;padding:18px 40px;text-align:center;\">" +
                "<p style=\"color:#aaa;font-size:12px;margin:0;\">LAK Chemicals &amp; Hardware &nbsp;|&nbsp; This is an automated message.</p></div></div></body></html>";
    }
}
