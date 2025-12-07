import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent],
  template: `
    <app-header></app-header>
    <main class="auth-page">
      <div class="auth-card">
        <h1>สมัครสมาชิก</h1>

        <label for="reg-username">Username</label>
        <input id="reg-username" type="text" placeholder="Username" />

        <label for="reg-email">Email</label>
        <input id="reg-email" type="email" placeholder="Email" />

        <label for="reg-password">Password</label>
        <input id="reg-password" type="password" placeholder="Password" />

        <div class="actions">
          <button class="primary" (click)="onRegister()">Register</button>
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
    .auth-card a { color:var(--link-color, #3366ff); }
    .auth-card .actions { text-align:left; margin-top:12px; }
    .auth-card .actions .primary { width:100%; display:block; }
    .auth-card .actions .actions-note { margin-top:12px; text-align:center; }
  `]
})
export class RegisterComponent {
  constructor(private router: Router) {}

  onRegister() {
    // TODO: perform registration logic/validation
    // After successful registration, redirect to login page
    this.router.navigate(['/login']);
  }
}
