import requests
from django.shortcuts import render, redirect


# 1. პროდუქტების სია

def product_list(request):
    query = request.GET.get('search')
    cat_id = request.GET.get('category')  # ვიღებთ კატეგორიის ID-ს URL-დან
    
    # განვსაზღვროთ რომელი URL გამოვიყენოთ API-სთვის

    if query:
        url = f"https://api.everrest.educata.dev/shop/products/search?keywords={query}&page_index=1&page_size=20"
    elif cat_id:
        url = f"https://api.everrest.educata.dev/shop/products/category/{cat_id}?page_index=1&page_size=20"
    else:
        url = "https://api.everrest.educata.dev/shop/products/all?page_index=1&page_size=20"
    
    products = []
    try:
        response = requests.get(url)
        data = response.json()
        products_raw = data.get('products', [])
        
        for p in products_raw:
            p['p_id'] = p.get('_id')
            price_data = p.get('price', {})
            if isinstance(price_data, dict):
                p['price'] = price_data.get('current', 0)
            products.append(p)
            
    except Exception as e:
        print(f"Error: {e}")

    # ვაწვდით cat_id-ს შაბლონს, რომ "active" კლასი მივანიჭოთ მენიუში

    return render(request, 'shop/product/list.html', {
        'products': products, 
        'query': query,
        'current_cat': cat_id
    })

# 2. პროდუქტის დეტალები

def product_detail(request, id):
    url = f"https://api.everrest.educata.dev/shop/products/id/{id}"
    product = None
    try:
        response = requests.get(url)
        if response.status_code == 200:
            product = response.json()
            
            product['p_id'] = product.get('_id')
    except Exception as e:
        print(f"Error fetching product detail: {e}")

    return render(request, 'shop/product/detail.html', {'product': product})

# 3. კალათის ჩვენება

def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    for p_id, quantity in cart.items():
        url = f"https://api.everrest.educata.dev/shop/products/id/{p_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                p = response.json()
                price = p.get('price', {}).get('current', 0)
                item_total = price * quantity
                total_price += item_total
                
                cart_items.append({
                    'id': p_id,
                    'title': p.get('title'),
                    'price': price,
                    'quantity': quantity,
                    'total': item_total,
                    'image': p.get('images', [''])[0]
                })
        except:
            continue
            
    return render(request, 'shop/cart/detail.html', {
        'cart_items': cart_items, 
        'total_price': total_price
    })

# 4. კალათის განახლება

def update_cart(request, p_id, action):
    cart = request.session.get('cart', {})
    p_id = str(p_id)
    
    if action == 'increment':
        cart[p_id] = cart.get(p_id, 0) + 1
    elif p_id in cart:
        if action == 'decrement':
            cart[p_id] -= 1
            if cart[p_id] < 1:
                del cart[p_id]
        elif action == 'remove':
            del cart[p_id]
            
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('shop:cart_detail')



# 5. რეგისტრაცია

def register_user(request):
    message = ""
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        url = "https://api.everrest.educata.dev/shop/auth/register"
        
        # ვამატებთ სატესტო სახელს და გვარს

        payload = {
            "email": email,
            "password": password,
            "firstName": "User", 
            "lastName": "Test"
        }
        
        try:
            response = requests.post(url, json=payload)
            print(f"DEBUG: Status {response.status_code}, Response: {response.json()}")
            
            if response.status_code == 201:
                message = "რეგისტრაცია წარმატებულია! შეგიძლიათ შეხვიდეთ."
            else:
                data = response.json()
                # თუ API შეცდომას აბრუნებს 

                err = data.get('message', 'მონაცემები არასწორია')
                message = f"შეცდომა: {', '.join(err) if isinstance(err, list) else err}"
        except Exception as e:
            message = f"კავშირის შეცდომა: {e}"
            
    return render(request, 'shop/auth/register.html', {'message': message})

# 6. სისტემაში შესვლა

def login_user(request):
    message = ""
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        url = "https://api.everrest.educata.dev/shop/auth/login"
        
        try:
            response = requests.post(url, json={"email": email, "password": password})
            if response.status_code == 200:
                data = response.json()
                request.session['access_token'] = data.get('access_token')
                request.session['user_email'] = email 
                return redirect('shop:product_list')
            else:
                message = "მეილი ან პაროლი არასწორია."
        except:
            message = "სერვერთან კავშირი ვერ დამყარდა."
            
    return render(request, 'shop/auth/login.html', {'message': message})

# 7. სისტემიდან გამოსვლა

def logout_user(request):
    request.session.flush()
    return redirect('shop:product_list')
