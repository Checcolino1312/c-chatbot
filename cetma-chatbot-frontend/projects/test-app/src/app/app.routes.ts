import { Routes } from '@angular/router';
import { HomepageComponent } from './homepage/homepage.component';
import { BookingPageComponent } from './booking-page/booking-page.component';

export const routes: Routes = [
  { path: '', component: HomepageComponent },
  { path: 'prenotazioni', component: BookingPageComponent },
  { path: '**', redirectTo: '', pathMatch: 'full' }
];