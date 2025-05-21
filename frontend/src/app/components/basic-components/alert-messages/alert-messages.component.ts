import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'alertups-messages',
  templateUrl: './alert-messages.component.html',
  styleUrls: ['./alert-messages.component.scss']
})
export class AlertMessagesComponent {

  @Input() openModal: boolean = false;
  @Input() title: string = "";
  @Input() subtitle: string = "";
  @Input() icon: string = "";
  @Input() bPrimary: string = "NAVIGATION.CANCEL";
  @Input() bSecundary: string = "";
  @Input() isOptionButtons: boolean = false;
  @Input() basicActionCustom: boolean = false
  @Output() action = new EventEmitter();
  @Output() basicAction = new EventEmitter();
  @Output() closeModal = new EventEmitter();

  constructor() { }

  public buttonAction() {
    this.action.emit(null);
  }

  public closeOnlyModal() {
    this.closeModal.emit(null);
  }

  public basicActions(){
    this.basicAction.emit();
  }

  public closeOnlyModalMainCTA(){
    if(this.basicActionCustom){
      this.basicActions();
    }else{
      this.closeOnlyModal();
    }
  }
}
