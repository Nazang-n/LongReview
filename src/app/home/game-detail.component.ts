import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-game-detail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="detail-page">
      <div class="banner">
        <h1>ชื่อเกม (ID: {{ gameId }})</h1>
      </div>
      <div class="container">
        <div class="main-info">
           <h2>รายละเอียด</h2>
           <p>นี่คือเนื้อหาจำลองของเกม ID: {{ gameId }} ตัวเกมมีกราฟิกที่สวยงาม...</p>
           <button class="buy-btn">ซื้อเกม ฿1,590</button>
        </div>
        <div class="stats">
           <h3>สเปคขั้นต่ำ</h3>
           <ul>
             <li>OS: Windows 10</li>
             <li>RAM: 16 GB</li>
           </ul>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .detail-page { padding-top: 70px; }
    .banner { height: 300px; background: #333; color: white; display: flex; align-items: flex-end; padding: 30px; }
    .banner h1 { margin: 0; font-size: 3rem; }
    .container { display: flex; gap: 40px; max-width: 1000px; margin: 30px auto; padding: 0 20px; }
    .main-info { flex: 2; }
    .stats { flex: 1; background: #f9f9f9; padding: 20px; border-radius: 8px; }
    .buy-btn { background: #4CAF50; color: white; border: none; padding: 15px 30px; font-size: 1.2rem; border-radius: 5px; cursor: pointer; margin-top: 20px; }
  `]
})
export class GameDetailComponent implements OnInit {
  gameId: string | null = '';

  constructor(private route: ActivatedRoute) {}

  ngOnInit() {
    // รับค่า ID จาก URL มาแสดง
    this.gameId = this.route.snapshot.paramMap.get('id');
  }
}