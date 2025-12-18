import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';

import { AuthService, User } from '../services/auth.service';
import { Observable } from 'rxjs';
import { PLATFORM_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
  <header class="navbar">
    <div class="container-nav">
      <div class="logo-section" routerLink="/" style="cursor: pointer;">
        <div class="logo-icon"><img src="/Logo.png" alt="Logo"></div>
        <span class="brand-name">LongReview</span>
      </div>

      <nav class="nav-links">
        <a routerLink="/news" routerLinkActive="active">ข่าวสาร</a>
        <a routerLink="/games" routerLinkActive="active">เกมส์</a>
        <a routerLink="/favorites" routerLinkActive="active">รายการโปรด</a>
        <a *ngIf="isAdmin()" routerLink="/admin" routerLinkActive="active" class="admin-link">Admin</a>
      </nav>

      <div class="user-actions">
        <div class="search-box">
          <input type="text" placeholder="ค้นหา">
          <i class="pi pi-search"></i>
        </div>
        
        <ng-container *ngIf="currentUser$ | async as user; else loginLink">
           <div class="user-info">
             <span class="username">{{ user.username }}</span>
             <div class="profile-dropdown-wrapper">
               <a class="profile-icon" (click)="toggleDropdown($event)" title="Profile">
                <i class="pi pi-user"></i>
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
  </header>
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
  `]
})
export class HeaderComponent {
  currentUser$: Observable<User | null>;
  isBrowser: boolean;
  isDropdownOpen = false;

  constructor(
    private authService: AuthService,
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

  toggleDropdown(event: Event) {
    event.stopPropagation();
    this.isDropdownOpen = !this.isDropdownOpen;
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
    this.authService.logout();
    this.router.navigate(['/']);
  }
}
