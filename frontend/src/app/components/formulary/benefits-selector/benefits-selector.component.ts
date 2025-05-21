import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-benefits-selector',
  templateUrl: './benefits-selector.component.html',
  styleUrls: ['./benefits-selector.component.scss']
})
export class BenefitsSelectorComponent implements OnInit {

  @Output() goBack = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();
  @Input() imgSrc: string = "./assets/images/sharing-information_nobg.png";
  @Input() selectedButton: string = "";
  @Input() loading: boolean = false;
  public form: FormGroup = new FormGroup({});

  constructor(
    private formBuilder: FormBuilder,
  ) { }

  ngOnInit() {
    this.setForm();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      selectedButton: [this.selectedButton, Validators.required],
    });
  }

  public back() {
    this.goBack.emit();
  }

  public closeIt() {
    this.close.emit();
  }

  public goNext() {
    this.loading = true;
    setTimeout(() => {
      this.next.emit();
    }, 3000);
  }

  public setControlValue(value: string) {
    this.form.controls["selectedButton"].setValue(value);
  }

}
