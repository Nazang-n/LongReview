import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

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
        <a class="profile-icon" routerLink="/login" title="Profile">👤</a>
      </div>
    </div>
  </header>
  `,
  // styles are global (in src/styles.css)
})
export class HeaderComponent { }
