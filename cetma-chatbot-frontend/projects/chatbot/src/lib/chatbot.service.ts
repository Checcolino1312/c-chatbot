import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ChatbotService {
  private rasaApiUrl = 'http://localhost:8099/webhooks/rest/webhook'; // Endpoint Rasa
  //private actionApiUrl = 'https://80.241.139.36:8098/webhooks/rest/webhook'; // Endpoint Action Server

  constructor(private http: HttpClient) { }

  // Metodo standard per comunicare con il bot
  sendMessage(sender: string, message: string): Observable<any> {
    const payload = { sender, message };
    return this.http.post<any>(this.rasaApiUrl, payload);
  }

  // Metodo per inviare richieste direttamente all'action server
  /*callActionServer(actionName: string, payload: any): Observable<any> {
    const url = `${this.actionApiUrl}/${actionName}`;
    return this.http.post<any>(url, payload);
  }*/
}
