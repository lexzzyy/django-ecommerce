$('.plus-cart').click(function(){
  var id = $(this).attr("pid").toString();
  var eml = this.parentNode.children[2];
  console.log("pid = ",id)
  $.ajax({
    type: "GET",
    url: "/pluscart",
    data: {
      prod_id: id
    },
    success: function(data){
      console.log("data = ",data);
      eml.innerText = data.quantity;
      document.getElementById("amount").innerText = data.amount;
      document.getElementById("totalamount").innerText = data.totalamount;
    }
  })
})

$('.minus-cart').click(function(){
  var id = $(this).attr("pid").toString();
  var eml = this.parentNode.children[2];
  console.log("pid = ",id)
  $.ajax({
    type: "GET",
    url: "/minuscart",
    data: {
      prod_id: id
    },
    success: function(data){
      console.log("data = ",data);
      if(data.quantity > 0){
        eml.innerText = data.quantity;
      } else {
        $(this).closest('.row').remove();
      }
      document.getElementById("amount").innerText = data.amount;
      document.getElementById("totalamount").innerText = data.totalamount;
    }
  })
})

$('.remove-cart').click(function(){
  var id = $(this).attr("pid").toString();
  var eml = this;
  console.log("pid = ",id)
  $.ajax({
    type: "GET",
    url: "/removecart", 
    data: {
      prod_id: id
    },
    success: function(data){
      document.getElementById("amount").innerText = data.amount;
      document.getElementById("totalamount").innerText = data.totalamount;
      $(eml).closest('.row').remove(); 
    }
  })
})
