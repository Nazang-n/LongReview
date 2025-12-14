import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

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
      </nav>

      <div class="user-actions">
        <div class="search-box">
          <input type="text" placeholder="ค้นหา">
          <span class="search-icon">🔍</span>
        </div>
        
        <ng-container *ngIf="currentUser$ | async as user; else loginLink">
           <div class="user-info">
             <span class="username">{{ user.username }}</span>
             <a class="profile-icon" routerLink="/profile" title="Profile">👤</a>
           </div>
        </ng-container>
        <ng-template #loginLink>
           <a class="profile-icon" routerLink="/login" title="Login">👤</a>
        </ng-template>
        
      </div>
    </div>
  </header>
  `,
  // styles are global (in src/styles.css) or we can add inline styles for .username
  styles: [`
    .user-info { display: flex; align-items: center; gap: 10px; color: white; }
    .username { font-weight: 500; font-size: 0.9rem; }
  `]
})
export class HeaderComponent {
  currentUser$: Observable<User | null>;
  isBrowser: boolean;

  constructor(
    private authService: AuthService,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.currentUser$ = this.authService.getCurrentUser();
    this.isBrowser = isPlatformBrowser(platformId);
  }
}
