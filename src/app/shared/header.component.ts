import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { DialogModule } from 'primeng/dialog';

import { AuthService, User } from '../services/auth.service';
import { ProfileService, UserProfile } from '../services/profile.service';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { PLATFORM_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule, DialogModule],
  template: `
  <header class="navbar">
    <div class="container-nav">
      <!-- Hamburger button (mobile only) -->
      <button class="hamburger" (click)="toggleMobileMenu()" [class.open]="isMobileMenuOpen" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>

      <div class="logo-section" routerLink="/" style="cursor: pointer;">
        <div class="logo-icon"><img src="/Logo.png" alt="Logo"></div>
        <span class="brand-name">LongReview</span>
      </div>

      <!-- Desktop nav -->
      <nav class="nav-links">
        <a routerLink="/news" routerLinkActive="active">ข่าวสาร</a>
        <a routerLink="/games" routerLinkActive="active">เกม</a>
        <a routerLink="/favorites" routerLinkActive="active">รายการโปรด</a>
        <a *ngIf="isAdmin()" routerLink="/admin" routerLinkActive="active" class="admin-link">ผู้ดูแลระบบ</a>
      </nav>

      <div class="user-actions">
        <ng-container *ngIf="currentUser$ | async as user; else loginLink">
           <div class="user-info">
             <span class="username">{{ user.username }}</span>
             <div class="profile-dropdown-wrapper">
               <a class="profile-icon" (click)="toggleDropdown($event)" title="Profile">
                <img *ngIf="hasAvatar()" [src]="getAvatarUrl()" [alt]="user.username" class="avatar-image">
                <i *ngIf="!hasAvatar()" class="pi pi-user"></i>
               </a>
               <div class="dropdown-menu" [class.show]="isDropdownOpen">
                 <a class="dropdown-item" (click)="navigateToProfile()">
                  <i class="pi pi-user"></i>
                   <span>โปรไฟล์ของฉัน</span>
                 </a>
                 <a *ngIf="isAdmin()" class="dropdown-item" (click)="navigateToAdmin()">
                  <i class="pi pi-cog"></i>
                   <span>Admin Panel</span>
                 </a>
                 <div class="dropdown-divider"></div>
                 <a class="dropdown-item" (click)="logout()">
                   <i class="pi pi-sign-out"></i>
                   <span>ออกจากระบบ</span>
                 </a>
               </div>
             </div>
           </div>
        </ng-container>
        <ng-template #loginLink>
           <a class="profile-icon" routerLink="/login" title="Login">
             <i class="pi pi-user"></i>
           </a>
        </ng-template>
      </div>
    </div>

    <!-- Mobile nav drawer -->
    <div class="mobile-nav" [class.open]="isMobileMenuOpen">
      <a routerLink="/news" routerLinkActive="active" (click)="closeMobileMenu()">ข่าวสาร</a>
      <a routerLink="/games" routerLinkActive="active" (click)="closeMobileMenu()">เกม</a>
      <a routerLink="/favorites" routerLinkActive="active" (click)="closeMobileMenu()">รายการโปรด</a>
      <a *ngIf="isAdmin()" routerLink="/admin" routerLinkActive="active" (click)="closeMobileMenu()">ผู้ดูแลระบบ</a>
    </div>
  </header>

  <!-- Logout Confirmation Dialog -->
  <p-dialog 
    [(visible)]="showLogoutDialog" 
    [modal]="true" 
    [closable]="false"
    [style]="{width: '400px'}"
    header="ยืนยันการออกจากระบบ">
    <p style="margin: 0; padding: 16px 0;">คุณต้องการออกจากระบบหรือไม่?</p>
    <ng-template pTemplate="footer">
      <button 
        class="btn-cancel" 
        (click)="showLogoutDialog = false"
        style="padding: 8px 16px; margin-right: 8px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">
        ยกเลิก
      </button>
      <button 
        class="btn-confirm" 
        (click)="confirmLogout()"
        style="padding: 8px 16px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
        ออกจากระบบ
      </button>
    </ng-template>
  </p-dialog>

  <!-- Logout Success Dialog -->
  <p-dialog 
    [(visible)]="showLogoutSuccessDialog" 
    [modal]="true" 
    [closable]="false"
    [style]="{width: '400px'}">
    <ng-template pTemplate="header">
      <div style="display: flex; align-items: center; gap: 8px;">
        <i class="pi pi-check-circle" style="color: #28a745; font-size: 1.5rem;"></i>
        <span style="font-weight: 600; font-size: 1.1rem;">ออกจากระบบสำเร็จ</span>
      </div>
    </ng-template>
    <p style="margin: 0; padding: 16px 0;">คุณได้ออกจากระบบเรียบร้อยแล้ว</p>
    <ng-template pTemplate="footer">
      <button 
        class="btn-confirm" 
        (click)="handleLogoutSuccess()"
        style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
        ตกลง
      </button>
    </ng-template>
  </p-dialog>
  `,
  styles: [`
    .user-info { 
      display: flex; 
      align-items: center; 
      gap: 10px; 
      color: white; 
      position: relative;
    }
    .username { 
      font-weight: 500; 
      font-size: 0.9rem; 
    }
    .profile-dropdown-wrapper {
      position: relative;
    }
    .profile-icon {
      cursor: pointer;
      user-select: none;
    }
    .avatar-image {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      object-fit: cover;
      border: 2px solid rgba(255, 255, 255, 0.3);
      transition: border-color 0.2s ease;
    }
    .avatar-image:hover {
      border-color: rgba(255, 255, 255, 0.8);
    }
    .dropdown-menu {
      position: absolute;
      top: calc(100% + 8px);
      right: 0;
      background: white;
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      min-width: 160px;
      opacity: 0;
      visibility: hidden;
      transform: translateY(-10px);
      transition: all 0.2s ease;
      z-index: 1000;
    }
    .dropdown-menu.show {
      opacity: 1;
      visibility: visible;
      transform: translateY(0);
    }
    .dropdown-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      color: #333;
      text-decoration: none;
      cursor: pointer;
      transition: background-color 0.2s ease;
      font-size: 0.85rem;
    }
    .dropdown-item:first-child {
      border-radius: 6px 6px 0 0;
    }
    .dropdown-item:last-child {
      border-radius: 0 0 6px 6px;
    }
    .dropdown-item:hover {
      background-color: #f3f4f6;
    }
    .dropdown-icon {
      font-size: 1rem;
    }
    .dropdown-divider {
      height: 1px;
      background-color: #e5e7eb;
      margin: 2px 0;
    }

    /* Hamburger button */
    .hamburger {
      display: none;
      flex-direction: column;
      justify-content: space-between;
      width: 24px;
      height: 18px;
      background: transparent;
      border: none;
      cursor: pointer;
      padding: 0;
      margin-right: 15px;
    }
    .hamburger span {
      display: block;
      height: 2px;
      width: 100%;
      background: white;
      border-radius: 2px;
      transition: all 0.3s ease;
      transform-origin: center;
    }
    /* Animate to X when open */
    .hamburger.open span:nth-child(1) { transform: translateY(8px) rotate(45deg); }
    .hamburger.open span:nth-child(2) { opacity: 0; transform: scaleX(0); }
    .hamburger.open span:nth-child(3) { transform: translateY(-8px) rotate(-45deg); }

    /* Mobile nav drawer */
    .mobile-nav {
      display: none;
      flex-direction: column;
      background: #2b2b2b;
      position: absolute;
      top: var(--header-height, 70px);
      left: 0;
      width: 100%;
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.35s ease, padding 0.3s ease;
      z-index: 999;
      border-top: 1px solid #3a3a3a;
    }
    .mobile-nav.open {
      max-height: 400px;
      padding: 8px 0 16px;
    }
    .mobile-nav a {
      color: #ccc;
      text-decoration: none;
      padding: 14px 24px;
      font-size: 1.05rem;
      border-bottom: 1px solid #3a3a3a;
      transition: background 0.2s, color 0.2s;
    }
    .mobile-nav a:last-child { border-bottom: none; }
    .mobile-nav a:hover, .mobile-nav a.active {
      color: #fff;
      background: #383838;
    }

    /* Responsive breakpoint */
    @media (max-width: 768px) {
      .hamburger { display: flex; }
      .mobile-nav { display: flex; }
      .username { display: none; }
    }
  `]
})
export class HeaderComponent implements OnInit, OnDestroy {
  currentUser$: Observable<User | null>;
  isBrowser: boolean;
  isDropdownOpen = false;
  isMobileMenuOpen = false;
  showLogoutDialog = false;
  showLogoutSuccessDialog = false;
  userProfile: UserProfile | null = null;
  private destroy$ = new Subject<void>();

  constructor(
    private authService: AuthService,
    private profileService: ProfileService,
    private router: Router,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.currentUser$ = this.authService.getCurrentUser();
    this.isBrowser = isPlatformBrowser(platformId);

    // Close dropdown when clicking outside
    if (this.isBrowser) {
      document.addEventListener('click', (event) => {
        const target = event.target as HTMLElement;
        if (!target.closest('.profile-dropdown-wrapper')) {
          this.isDropdownOpen = false;
        }
      });
    }
  }

  ngOnInit(): void {
    // Subscribe to current user and load profile
    this.currentUser$.pipe(takeUntil(this.destroy$)).subscribe(user => {
      if (user) {
        this.loadUserProfile(user.id);
      } else {
        this.userProfile = null;
      }
    });

    // Listen to profile updates from other components
    if (this.isBrowser) {
      window.addEventListener('profileUpdated', () => {
        const user = this.authService.getCurrentUserValue();
        if (user) {
          this.loadUserProfile(user.id);
        }
      });
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadUserProfile(userId: number): void {
    this.profileService.getProfile(userId).subscribe({
      next: (profile) => {
        this.userProfile = profile;
      },
      error: (err) => {
        console.error('Error loading user profile in header:', err);
      }
    });
  }

  hasAvatar(): boolean {
    return this.userProfile?.avatar_url !== null && this.userProfile?.avatar_url !== undefined && this.userProfile?.avatar_url !== '';
  }

  getAvatarUrl(): string {
    return this.userProfile?.avatar_url || '';
  }

  toggleDropdown(event: Event) {
    event.stopPropagation();
    this.isDropdownOpen = !this.isDropdownOpen;
  }

  toggleMobileMenu() {
    this.isMobileMenuOpen = !this.isMobileMenuOpen;
  }

  closeMobileMenu() {
    this.isMobileMenuOpen = false;
  }

  isAdmin(): boolean {
    return this.authService.isAdmin();
  }

  navigateToProfile() {
    this.isDropdownOpen = false;
    this.router.navigate(['/profile']);
  }

  navigateToAdmin() {
    this.isDropdownOpen = false;
    this.router.navigate(['/admin']);
  }

  logout() {
    this.isDropdownOpen = false;
    this.showLogoutDialog = true;
  }

  confirmLogout() {
    this.showLogoutDialog = false;
    this.authService.logout();
    this.showLogoutSuccessDialog = true;
  }

  handleLogoutSuccess() {
    this.showLogoutSuccessDialog = false;
    this.router.navigate(['/']);
  }
}
