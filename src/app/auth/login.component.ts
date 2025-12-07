import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent],
  template: `
    <app-header></app-header>
    <main class="auth-page">
      <div class="auth-card">
        <h1>ยินดีต้อนรับสู่ LongReview</h1>
        <label for="login-email">Email</label>
        <input id="login-email" type="email" placeholder="Email" />

        <label for="login-password">Password</label>
        <input id="login-password" type="password" placeholder="Password" />

        <button class="primary">Login</button>
        <p style="margin-top:12px">ยังไม่มีบัญชี? <a routerLink="/register">สมัครสมาชิก</a></p>
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
    .auth-card a { color:var(--link-color, #3366ff); }
  `]
})
export class LoginComponent {}
