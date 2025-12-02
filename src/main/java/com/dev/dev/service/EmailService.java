package com.dev.dev.service;

import com.dev.dev.dto.email.EmailQARequest;
import com.sendgrid.*;
import com.sendgrid.helpers.mail.Mail;
import com.sendgrid.helpers.mail.objects.Email;
import com.sendgrid.helpers.mail.objects.Personalization;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;

@Service
public class EmailService {
    private final String apiKey = "SENDGRID_API_KEY_REMOVED";

    public void sendQAEmail(
            String userName,
            String userEmail,
            String title,
            String content,
            String templateId
    ) {
        Email from = new Email("noreply@together1.kro.kr");  // SendGrid에서 인증된 발신자
        Email to = new Email("jyk9435@chungbuk.ac.kr");            // 관리자 이메일
        Mail mail = new Mail();
        mail.setFrom(from);
        mail.setTemplateId(templateId);
        Personalization personalization = new Personalization();
        personalization.addTo(to);
        personalization.addDynamicTemplateData("username", userName);
        personalization.addDynamicTemplateData("userEmail", userEmail);
        personalization.addDynamicTemplateData("title", title);
        personalization.addDynamicTemplateData("content", content);
        mail.addPersonalization(personalization);
        SendGrid sg = new SendGrid(apiKey);
        try {
            Request request = new Request();
            request.setMethod(Method.POST);
            request.setEndpoint("mail/send");
            request.setBody(mail.build());
            sg.api(request);
        } catch (Exception e) {
            throw new RuntimeException("QA 이메일 전송 실패", e);
        }
    }
}
