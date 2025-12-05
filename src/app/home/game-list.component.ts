import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-game-list',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="layout">
      <aside class="sidebar" [class.closed]="!isFilterOpen">
        <div class="sidebar-header">
          <h3>ตัวกรอง (Filter)</h3>
          <button (click)="toggleFilter()" class="close-icon">✕</button>
        </div>
        <div class="filter-group">
          <label>หมวดหมู่</label>
          <div><input type="checkbox"> Action</div>
          <div><input type="checkbox"> RPG</div>
          <div><input type="checkbox"> Strategy</div>
        </div>
      </aside>

      <main class="content">
        <button *ngIf="!isFilterOpen" (click)="toggleFilter()" class="open-filter-btn">
          📂 เปิดตัวกรอง
        </button>

        <h1>รายการเกมทั้งหมด</h1>
        <div class="game-grid">
          <div class="game-card" *ngFor="let i of [1,2,3,4,5,6]" [routerLink]="['/game', i]">
            <div class="game-img">IMG</div>
            <div class="card-info">
              <h3>Game Title {{i}}</h3>
              <span>⭐⭐⭐⭐</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  `,
  styles: [`
    .layout { display: flex; padding-top: 70px; min-height: 100vh; }
    
    /* Sidebar Styles */
    .sidebar { width: 250px; background: #f4f4f4; padding: 20px; border-right: 1px solid #ddd; transition: 0.3s; overflow: hidden; white-space: nowrap;}
    .sidebar.closed { width: 0; padding-left: 0; padding-right: 0; border: none; }
    .sidebar-header { display: flex; justify-content: space-between; margin-bottom: 20px; }
    .close-icon { background: none; border: none; font-size: 1.2rem; cursor: pointer; }
    
    /* Main Content Styles */
    .content { flex: 1; padding: 20px; }
    .open-filter-btn { background: #333; color: white; border: none; padding: 8px 15px; cursor: pointer; margin-bottom: 15px; border-radius: 4px; }
    
    .game-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
    .game-card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); cursor: pointer; transition: transform 0.2s; }
    .game-card:hover { transform: translateY(-5px); }
    .game-img { height: 180px; background: linear-gradient(45deg, #ff9a9e, #fad0c4); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }
    .card-info { padding: 10px; }
  `]
})
export class GameListComponent {
  isFilterOpen = true; // สถานะเริ่มต้นเปิดอยู่

  toggleFilter() {
    this.isFilterOpen = !this.isFilterOpen;
  }
}