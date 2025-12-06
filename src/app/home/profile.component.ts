import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, HeaderComponent, FooterComponent],
  template: `
    <app-header></app-header>
    <div class="profile-page" style="margin-top: var(--header-height); padding: 20px; min-height: calc(100vh - var(--header-height));">
      <h1>โปรไฟล์ของฉัน</h1>
      <p>ข้อมูลผู้ใช้และการตั้งค่าจะแสดงที่นี่</p>
    </div>
    <app-footer></app-footer>
  `
})
export class ProfileComponent {}
