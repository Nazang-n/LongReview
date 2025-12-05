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
  { path: '', component: HomeComponent }, // ปิดปีกกาตรงนี้ให้เรียบร้อย
  
  // หน้าอื่นๆ (เป็นพี่น้องกับหน้า Home ไม่ใช่ลูก)
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
    // ไม่ต้องใส่ Component ในนี้ (แม้จะเป็น Standalone) 
    // เพราะเราใช้มันแค่ในตัวแปร routes ด้านบน
  ],
  exports: [RouterModule]
})
export class AppRoutingModule { }