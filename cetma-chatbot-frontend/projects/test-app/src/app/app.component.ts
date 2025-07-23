import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { ChatbotComponent } from '../../../chatbot/src/lib/chatbot.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, ChatbotComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent { }
