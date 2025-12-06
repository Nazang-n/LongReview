// app-routing.module.ts
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Import Component เข้ามาเพื่อนำไปใช้ใน routes
import { HomeComponent } from './home/home.component';
import { NewsComponent } from './home/news.component';
import { FavoritesComponent } from './home/favorites.component';
import { GameListComponent } from './home/game-list.component';
import { GameDetailComponent } from './home/game-detail.component';

const routes: Routes = [
  // หน้าแรก (Home)
  { path: '', component: HomeComponent }, 
  
  { path: 'news', component: NewsComponent },
  { path: 'favorites', component: FavoritesComponent },
  { path: 'games', component: GameListComponent },
  { path: 'game/:id', component: GameDetailComponent },
  
  // (Optional) กรณีพิมพ์ URL ผิดให้กลับไปหน้าแรก
  { path: '**', redirectTo: '' }
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes) 
  ],
  exports: [RouterModule]
})
export class AppRoutingModule { }