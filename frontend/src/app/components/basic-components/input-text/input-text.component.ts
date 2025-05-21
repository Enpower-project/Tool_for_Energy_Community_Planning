import { Component, EventEmitter, Input, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'textups',
  templateUrl: './input-text.component.html',
  styleUrls: ['./input-text.component.scss']
})
export class InputTextComponent implements OnInit {

  @Input() initialValue: string = "";
  @Input() placeholder: string = "";
  @Input() firstIcon?: string;
  @Input() finalIcon?: string;
  @Input() topText?: string;
  @Input() hintText?: string;
  @Input() type: string = "text";
  @Input() isPassword?: boolean = false;
  @Input() showPass: boolean = false;
  @Input() compact: boolean = false
  @Input() noPadding:boolean = false;
  @Output() changeValue = new EventEmitter();
  @Output() finalIconAction = new EventEmitter();

  form: FormGroup = new FormGroup({});

  constructor(
    private formBuilder: FormBuilder,
  ) { }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['initialValue'] && this.form.controls["valor"]) {
      this.form.controls['valor'].setValue(this.initialValue);
    }
  }

  ngOnInit() {
    this.setForm();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      valor: [this.initialValue, Validators.required],
    });
    this.form.controls['valor'].valueChanges.subscribe((res) => this.changeValue.next(res))
  }

  public showPassword() {
    this.showPass = !this.showPass;
    if (this.type === "password") {
      this.type = "text";
    } else {
      this.type = "password"
    }
  }

  public save(){
    this.finalIconAction.emit(this.form.controls['valor'].value)
  }

}
