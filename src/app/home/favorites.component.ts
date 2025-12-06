import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';

@Component({
  selector: 'app-favorites',
  standalone: true,
  imports: [CommonModule, HeaderComponent, FooterComponent],
  template: `
    <app-header></app-header>
    <div class="page-container">
      <h1>❤️ รายการโปรดของคุณ</h1>
      <div class="fav-grid">
        <div class="fav-card" *ngFor="let game of ['Elden Ring', 'GTA V', 'Valorant']">
          <div class="fav-img"></div>
          <h3>{{ game }}</h3>
          <button class="remove-btn">ลบออก</button>
        </div>
      </div>
    </div>
    <app-footer></app-footer>
  `,
  styles: [`
    .page-container { padding: 100px 10% 20px; }
    .fav-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
    .fav-card { background: white; padding: 10px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .fav-img { height: 150px; background: #333; margin-bottom: 10px; border-radius: 4px; }
    .remove-btn { background: #ff4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
  `]
})
export class FavoritesComponent {}