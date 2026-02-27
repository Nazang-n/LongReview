import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, FooterComponent],
  template: `
    <main class="auth-page">
      <div class="auth-card">
        <h1>สมัครสมาชิก</h1>

        <label for="reg-username">Username</label>
        <input id="reg-username" type="text" placeholder="Username" [(ngModel)]="username" />

        <label for="reg-email">Email</label>
        <input id="reg-email" type="email" placeholder="Email" [(ngModel)]="email" />

        <label for="reg-password">Password</label>
        <input id="reg-password" type="password" placeholder="Password" [(ngModel)]="password" />

        <div class="error-message" *ngIf="errorMessage">
          {{ errorMessage }}
        </div>

        <div class="actions">
          <button class="primary" (click)="onRegister()" [disabled]="isLoading">
            {{ isLoading ? 'กำลังสมัครสมาชิก...' : 'Register' }}
          </button>
          <p class="actions-note">มีบัญชีแล้ว? <a routerLink="/login">เข้าสู่ระบบ</a></p>
        </div>
      </div>
    </main>
    <app-footer></app-footer>
  `,
  styles: [`
    .auth-page { margin-top: var(--header-height); min-height: calc(100vh - var(--header-height)); display:flex; align-items:flex-start; justify-content:center; padding:40px 10px; box-sizing:border-box; }
    .auth-card { width:100%; max-width:420px; background:#fff; padding:28px; border-radius:8px; box-shadow:0 8px 24px rgba(0,0,0,0.06); text-align:left; }
    .auth-card h1 { font-size:1.4rem; margin-bottom:18px; text-align:center; }
    .auth-card label { display:block; font-weight:600; margin-top:10px; margin-bottom:6px; font-size:0.95rem; }
    .auth-card input { width:100%; padding:10px 12px; margin:0 0 8px 0; border:1px solid #ddd; border-radius:6px; box-sizing:border-box; }
    .auth-card .primary { width:100%; padding:10px; margin-top:10px; background:#333; color:#fff; border:none; border-radius:6px; cursor:pointer; }
    .auth-card .primary:disabled { opacity:0.6; cursor:not-allowed; }
    .auth-card a { color:var(--link-color, #3366ff); }
    .auth-card .actions { text-align:left; margin-top:12px; }
    .auth-card .actions .primary { width:100%; display:block; }
    .auth-card .actions .actions-note { margin-top:12px; text-align:center; }
    .error-message { color: #d32f2f; font-size: 0.9rem; margin: 10px 0; padding: 8px; background: #ffebee; border-radius: 4px; }
  `]
})
export class RegisterComponent {
  username: string = '';
  email: string = '';
  password: string = '';
  isLoading: boolean = false;
  errorMessage: string = '';

  constructor(private authService: AuthService, private router: Router) { }

  onRegister() {
    // Validate inputs
    if (!this.username || !this.email || !this.password) {
      this.errorMessage = 'กรุณากรอกข้อมูลให้ครบถ้วน';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.register({
      username: this.username,
      email: this.email,
      password: this.password
    }).subscribe({
      next: (user) => {
        // Registration successful, redirect to login or home
        this.router.navigate(['/login']);
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Registration error:', error);

        // Handle validation errors from FastAPI/Pydantic
        if (error.error?.detail) {
          // Check if detail is an array (validation errors)
          if (Array.isArray(error.error.detail)) {
            // Extract the first error message
            const firstError = error.error.detail[0];
            if (firstError.msg) {
              // Extract the actual message from "Value error, <message>" format
              const msg = firstError.msg;
              if (msg.includes('Value error, ')) {
                this.errorMessage = msg.replace('Value error, ', '');
              } else {
                this.errorMessage = msg;
              }
            } else {
              this.errorMessage = 'เกิดข้อผิดพลาดในการตรวจสอบข้อมูล';
            }
          } else if (typeof error.error.detail === 'string') {
            // Handle string error messages (like "อีเมลนี้ถูกใช้งานแล้ว")
            this.errorMessage = error.error.detail;
          } else {
            this.errorMessage = 'เกิดข้อผิดพลาด';
          }
        } else if (error.message) {
          this.errorMessage = error.message;
        } else {
          this.errorMessage = 'เกิดข้อผิดพลาด กรุณาลองใหม่';
        }
      }
    });
  }
}

