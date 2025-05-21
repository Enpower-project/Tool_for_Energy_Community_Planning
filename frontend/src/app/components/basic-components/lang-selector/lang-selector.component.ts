import { Component, ElementRef, EventEmitter, HostListener, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'lang-selectups',
  templateUrl: './lang-selector.component.html',
  styleUrls: ['./lang-selector.component.scss']
})
export class LangSelectorComponent implements OnInit {

  @Input() homeMode: boolean = false;
  @Input() sidebarMode: boolean = false;
  @Input() showLangSelector: boolean = false;
  @Output() changeShowLang = new EventEmitter()

  public langs = [
    {
      name: "LANGUAGE_MENU.ENGLISH",
      value: "en",
      icon: "UnitedKingdom.svg"
    },
    {
      name: "LANGUAGE_MENU.SPANISH",
      value: "es",
      icon: "Spain.svg"
    },
    {
      name: "LANGUAGE_MENU.GERMAN",
      value: "de",
      icon: "Germany.svg"
    },
    {
      name: "LANGUAGE_MENU.ITALIAN",
      value: "it",
      icon: "Italy.svg"
    },
    {
      name: "LANGUAGE_MENU.SWEDISH",
      value: "sv",
      icon: "Sweden.svg"
    },
    {
      name: "LANGUAGE_MENU.BASQUE",
      value: "eu",
      icon: "Basque.svg"
    },
  ]

  form: FormGroup = new FormGroup({});

  constructor(
    private formBuilder: FormBuilder,
    private translate: TranslateService,
    private eRef: ElementRef,

  ) { }

  ngOnInit() {
    this.setForm();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      lang: [this.translate.currentLang, Validators.required],
    });
    this.form.controls['lang'].valueChanges.subscribe(() => { this.changeLang() })
  }

  selectPCLang(lang: string) {
    this.changeShowLangSelector();
    this.form.controls['lang'].setValue(lang);
  }

  public changeShowLangSelector() {
    this.changeShowLang.next(!this.showLangSelector);
  }

  changeLang() {
    this.translate.use(this.form.controls['lang'].value);
  }


  @HostListener('document:click', ['$event'])
  public clickFuera(event: any) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.changeShowLang.next(false);
    }
  }


}
