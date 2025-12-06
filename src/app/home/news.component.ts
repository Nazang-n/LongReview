import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from "../shared/header.component";
import { FooterComponent } from "../shared/footer.component";

@Component({
  selector: 'app-news',
  standalone: true,
  imports: [CommonModule, HeaderComponent, FooterComponent],
  template: `
  <app-header></app-header>
    <div class="page-container">
      <h1 class="page-title">ข่าวสารวงการเกม</h1>
      
      <div class="news-list">
        <div class="news-item" *ngFor="let i of [1, 2, 3, 4]">
          <div class="news-img"></div>
          <div class="news-content">
            <h3>อัปเดต Patch ใหญ่ {{i}}.0 มาแล้ว!</h3>
            <p class="date">5 ธันวาคม 2025</p>
            <p class="desc">รายละเอียดการอัปเดตใหม่ล่าสุด เพิ่มตัวละคร แผนที่ใหม่ และการปรับสมดุลเกม...</p>
            <button class="read-more">อ่านต่อ</button>
          </div>
        </div>
      </div>
    </div>
    <app-footer></app-footer>
  `,
  styles: [`
    .page-container {
      padding: 100px 20px 40px; /* เว้นที่ให้ Header */
      max-width: 900px;
      margin: 0 auto;
    }
    .page-title {
      border-bottom: 3px solid #ffca28;
      display: inline-block;
      margin-bottom: 30px;
      padding-bottom: 5px;
    }
    .news-item {
      display: flex;
      background: white;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
      margin-bottom: 20px;
      height: 180px;
    }
    .news-img {
      width: 250px;
      background: #ddd url('https://placehold.co/300x200?text=News') center/cover;
    }
    .news-content {
      padding: 20px;
      flex: 1;
      position: relative;
    }
    .news-content h3 { margin: 0 0 5px; color: #333; }
    .date { color: #888; font-size: 0.8rem; margin-bottom: 10px; }
    .desc { color: #555; font-size: 0.9rem; line-height: 1.4; }
    .read-more {
      position: absolute; bottom: 20px; right: 20px;
      background: #2b2b2b; color: white; border: none;
      padding: 5px 15px; border-radius: 4px; cursor: pointer;
    }
    .read-more:hover { background: #444; }

    @media (max-width: 600px) {
      .news-item { flex-direction: column; height: auto; }
      .news-img { width: 100%; height: 150px; }
    }
  `]
})
export class NewsComponent {}