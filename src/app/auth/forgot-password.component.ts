import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { PasswordModule } from 'primeng/password';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

@Component({
    selector: 'app-forgot-password',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        RouterModule,
        CardModule,
        InputTextModule,
        ButtonModule,
        PasswordModule,
        ToastModule,
        ProgressSpinnerModule
    ],
    providers: [MessageService],
    templateUrl: './forgot-password.component.html',
    styleUrls: ['./forgot-password.component.css']
})
export class ForgotPasswordComponent implements OnDestroy {
    // Step management
    currentStep: 'email' | 'code' | 'password' = 'email';

    // Form data
    email = '';
    code = '';
    newPassword = '';
    confirmPassword = '';

    // State
    isLoading = false;
    resetToken = '';

    // Countdown timer
    countdownMinutes = 10;
    countdownSeconds = 0;
    countdownInterval: any;

    private apiUrl = 'http://localhost:8000/api/auth';

    constructor(
        private http: HttpClient,
        private router: Router,
        private messageService: MessageService
    ) { }

    ngOnDestroy() {
        // Clear countdown timer when component is destroyed
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
    }

    startCountdown() {
        // Start 10 minute countdown
        this.countdownMinutes = 10;
        this.countdownSeconds = 0;

        this.countdownInterval = setInterval(() => {
            if (this.countdownSeconds === 0) {
                if (this.countdownMinutes === 0) {
                    // Time expired
                    clearInterval(this.countdownInterval);
                    this.messageService.add({
                        severity: 'error',
                        summary: 'รหัสหมดอายุ',
                        detail: 'รหัสยืนยันหมดอายุแล้ว กรุณาขอรหัสใหม่',
                        life: 5000
                    });
                    this.currentStep = 'email';
                    this.code = '';
                } else {
                    this.countdownMinutes--;
                    this.countdownSeconds = 59;
                }
            } else {
                this.countdownSeconds--;
            }
        }, 1000);
    }

    // Step 1: Request reset code
    async requestResetCode() {
        if (!this.email) {
            this.messageService.add({
                severity: 'warn',
                summary: 'กรุณากรอกอีเมล',
                detail: 'กรุณากรอกอีเมลของคุณ'
            });
            return;
        }

        this.isLoading = true;

        try {
            const response: any = await this.http.post(`${this.apiUrl}/forgot-password`, {
                email: this.email
            }).toPromise();

            this.messageService.add({
                severity: 'success',
                summary: 'ส่งรหัสยืนยันแล้ว',
                detail: response.message || 'กรุณาตรวจสอบอีเมลของคุณ'
            });

            this.currentStep = 'code';
            this.startCountdown(); // Start 10-minute countdown
        } catch (error: any) {
            this.messageService.add({
                severity: 'error',
                summary: 'เกิดข้อผิดพลาด',
                detail: error.error?.detail || 'ไม่สามารถส่งรหัสยืนยันได้'
            });
        } finally {
            this.isLoading = false;
        }
    }

    // Step 2: Verify code
    async verifyCode() {
        if (!this.code || this.code.length !== 6) {
            this.messageService.add({
                severity: 'warn',
                summary: 'รหัสไม่ถูกต้อง',
                detail: 'กรุณากรอกรหัสยืนยัน 6 หลัก'
            });
            return;
        }

        this.isLoading = true;

        try {
            const response: any = await this.http.post(`${this.apiUrl}/verify-reset-code`, {
                email: this.email,
                code: this.code
            }).toPromise();

            this.resetToken = response.token;
            this.messageService.add({
                severity: 'success',
                summary: 'ยืนยันสำเร็จ',
                detail: 'กรุณาตั้งรหัสผ่านใหม่'
            });

            this.currentStep = 'password';
        } catch (error: any) {
            this.messageService.add({
                severity: 'error',
                summary: 'รหัสไม่ถูกต้อง',
                detail: error.error?.detail || 'รหัสยืนยันไม่ถูกต้องหรือหมดอายุ'
            });
        } finally {
            this.isLoading = false;
        }
    }

    // Step 3: Reset password
    async resetPassword() {
        if (!this.newPassword || this.newPassword.length < 6) {
            this.messageService.add({
                severity: 'warn',
                summary: 'รหัสผ่านไม่ถูกต้อง',
                detail: 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร'
            });
            return;
        }

        if (this.newPassword !== this.confirmPassword) {
            this.messageService.add({
                severity: 'warn',
                summary: 'รหัสผ่านไม่ตรงกัน',
                detail: 'กรุณายืนยันรหัสผ่านให้ตรงกัน'
            });
            return;
        }

        this.isLoading = true;

        try {
            const response: any = await this.http.post(`${this.apiUrl}/reset-password`, {
                token: this.resetToken,
                new_password: this.newPassword
            }).toPromise();

            this.messageService.add({
                severity: 'success',
                summary: 'สำเร็จ!',
                detail: response.message || 'รีเซ็ตรหัสผ่านสำเร็จ'
            });

            // Redirect to login after 2 seconds
            setTimeout(() => {
                this.router.navigate(['/login']);
            }, 2000);
        } catch (error: any) {
            this.messageService.add({
                severity: 'error',
                summary: 'เกิดข้อผิดพลาด',
                detail: error.error?.detail || 'ไม่สามารถรีเซ็ตรหัสผ่านได้'
            });
        } finally {
            this.isLoading = false;
        }
    }

    // Go back to previous step
    goBack() {
        if (this.currentStep === 'code') {
            this.currentStep = 'email';
            this.code = '';
        } else if (this.currentStep === 'password') {
            this.currentStep = 'code';
            this.newPassword = '';
            this.confirmPassword = '';
        }
    }
}
