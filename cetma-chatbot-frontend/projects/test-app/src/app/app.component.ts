import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ChatbotComponent } from '../../../chatbot/src/lib/chatbot.component';
import { BookingComponent } from './booking/booking.component'; // Aggiungi import

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, ChatbotComponent, BookingComponent], // Aggiungi BookingComponent
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent { }