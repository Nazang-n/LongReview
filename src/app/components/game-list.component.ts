import { Component, OnInit } from '@angular/core';
import { GameService, Game } from '../services/game.service';

@Component({
    selector: 'app-game-list',
    template: `
    <div class="game-list-container">
      <h2>Games</h2>
      
      <div *ngIf="loading" class="loading">Loading games...</div>
      
      <div *ngIf="error" class="error">{{ error }}</div>
      
      <div class="games-grid" *ngIf="!loading && !error">
        <div class="game-card" *ngFor="let game of games">
          <img [src]="game.image_url || 'assets/placeholder-game.jpg'" [alt]="game.title">
          <h3>{{ game.title }}</h3>
          <p class="genre">{{ game.genre }}</p>
          <p class="description">{{ game.description }}</p>
          <div class="rating" *ngIf="game.rating">
            ⭐ {{ game.rating }}/10
          </div>
          <div class="meta">
            <span *ngIf="game.developer">{{ game.developer }}</span>
            <span *ngIf="game.release_date">{{ game.release_date }}</span>
          </div>
        </div>
      </div>
    </div>
  `,
    styles: [`
    .game-list-container {
      padding: 20px;
    }

    .loading, .error {
      text-align: center;
      padding: 40px;
      font-size: 18px;
    }

    .error {
      color: #e74c3c;
    }

    .games-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }

    .game-card {
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 15px;
      background: white;
      transition: transform 0.2s;
    }

    .game-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .game-card img {
      width: 100%;
      height: 150px;
      object-fit: cover;
      border-radius: 4px;
    }

    .game-card h3 {
      margin: 10px 0;
      font-size: 18px;
    }

    .genre {
      color: #666;
      font-size: 14px;
      margin: 5px 0;
    }

    .description {
      color: #333;
      font-size: 14px;
      margin: 10px 0;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .rating {
      font-weight: bold;
      color: #f39c12;
      margin: 10px 0;
    }

    .meta {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: #999;
      margin-top: 10px;
    }
  `]
})
export class GameListComponent implements OnInit {
    games: Game[] = [];
    loading = false;
    error: string | null = null;

    constructor(private gameService: GameService) { }

    ngOnInit(): void {
        this.loadGames();
    }

    loadGames(): void {
        this.loading = true;
        this.error = null;

        this.gameService.getGames().subscribe({
            next: (data) => {
                this.games = data;
                this.loading = false;
            },
            error: (err) => {
                this.error = 'Failed to load games. Please make sure the backend server is running.';
                this.loading = false;
                console.error('Error loading games:', err);
            }
        });
    }
}
