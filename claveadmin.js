function claveAdmin() {
    claveCorrecta = false;
    var clave = prompt(`¡Ingrese su Clave!`);
    cont = 1;
  
    while (claveCorrecta == false) {
      if (clave == "admin") {
        claveCorrecta = true;
      } else {
        clave = prompt(`¡Clave Incorrecta! ¡Ingrese su Clave Nuevamente!`);
        cont = cont + 1;
      }
  
      if (cont == 3) {
        alert("bueeee... ¡te dejamos pasar!");
        claveCorrecta = true;
      }
    }
  }