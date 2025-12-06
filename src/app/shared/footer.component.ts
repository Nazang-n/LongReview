import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [CommonModule],
  template: `
    <footer class="footer">
      <div class="container-footer">
        <div class="logo-section">
          <div class="logo-icon-sm">L</div>
          <span class="brand-name">LongReview</span>
        </div>
        <div class="footer-links">
          <p>About us | Privacy Policy | Terms of Service</p>
          <p class="copyright">© 2024 LongReview. All rights reserved.</p>
        </div>
      </div>
    </footer>
  `,
  styleUrls: ['../home/home.component.css']
})
export class FooterComponent {}
