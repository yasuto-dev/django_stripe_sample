from django.contrib import auth
import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  # new
from django.http.response import JsonResponse, HttpResponse  # updated
from django.views.decorators.csrf import csrf_exempt
from subscriptions.models import StripeCustomer  # new
from django.shortcuts import render, redirect,get_object_or_404
from .forms import UserForm
from .models import StripeCustomer
from django.shortcuts import render
from django.views.generic import DetailView, UpdateView, ListView, CreateView, base
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages


@login_required
def home(request):
    try:
        # Retrieve the subscription & product
        stripe_customer = StripeCustomer.objects.get(user=request.user)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
        product = stripe.Product.retrieve(subscription.plan.product)
        # Feel free to fetch any additional data from 'subscription' or 'product'
        # https://stripe.com/docs/api/subscriptions/object
        # https://stripe.com/docs/api/products/object


        return render(request, 'home.html', {
            'subscription': subscription,
            'product': product,
        })

    except StripeCustomer.DoesNotExist:
        return render(request, 'home.html')


@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)


@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        domain_url = 'http://localhost:8000/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=request.user.id if request.user.is_authenticated else None,
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancel/',
                payment_method_types=['card'],
                mode='subscription',
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,
                        'quantity': 1,
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})


@login_required
def success(request):
    return render(request, 'success.html')


@login_required
def cancel(request):
    return render(request, 'cancel.html')


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Fetch all the required data from session
        client_reference_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        stripe_subscription_id = session.get('subscription')

        # Get the user and create a new StripeCustomer
        user = User.objects.get(id=client_reference_id)
        StripeCustomer.objects.create(
            user=user,
            stripeCustomerId=stripe_customer_id,
            stripeSubscriptionId=stripe_subscription_id,
        )
        print(user.username + ' just subscribed.')

    return HttpResponse(status=200)


# ---------------------------MypageContextMixin----------------------------
class MypageContextMixin(base.ContextMixin):
    model = StripeCustomer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripecustomer_list'] = StripeCustomer.objects.filter(user=self.request.user)
        return context

# ---------------------------TopPage---------------------------------------
@method_decorator(login_required, name='dispatch')
class IndexView(MypageContextMixin, ListView):
    template_name = 'home.html'

home = IndexView.as_view()

# ------------------------MypageListView-------------------------------------
@method_decorator(login_required, name='dispatch')
class MypageListView(MypageContextMixin, ListView):
    template_name = 'mypage.html'
    model = StripeCustomer

mypage_list = MypageListView.as_view()

# ------------------------DetailView-----------------------------------------
@method_decorator(login_required, name='dispatch')
class MypageDetailView(MypageContextMixin, DetailView):
    model = StripeCustomer

mypage_detail = MypageDetailView.as_view()

# ---------------------------プロフィール登録-------------------------------------
@method_decorator(login_required, name='dispatch')
class PostCreate(MypageContextMixin, CreateView):
    template_name = 'create.html'
    form_class = UserForm
    model = StripeCustomer
    success_url = reverse_lazy('mypage')

    def has_add_permission(self, request):
        return False if self.model.objects.count() > 0 else True

    def form_valid(self, form):
        stripe_customer = form.save(commit=False)
        stripe_customer.user = self.request.user
        stripe_customer.save()
        messages.success(self.request, '登録されました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '再入力して下さい')
        return super().form_invalid(form)
       
post_create = PostCreate.as_view()

# ----------------------------プロフィール更新-------------------------------
@method_decorator(login_required, name='dispatch')
class PostUpdate(MypageContextMixin, UpdateView):
    template_name = 'create.html'
    form_class = UserForm
    model = StripeCustomer
    success_url = reverse_lazy('mypage')

    def form_valid(self, form):
        stripe_customer = form.save(commit=False)
        stripe_customer.user = self.request.user
        stripe_customer.save()
        messages.success(self.request, '更新しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '再入力して下さい')
        return super().form_invalid(form)

post_update = PostUpdate.as_view()

# ------------------------------------------------------------------------


@login_required 
def confirm(request):
    try:
        StripeCustomer.objects.get(user=request.user)
        params = {'message': '設定一覧'}
        return render(request, 'confirm.html', params)

    except StripeCustomer.DoesNotExist:
        return render(request, 'home.html')




def list(request):
    data = StripeCustomer.objects.all()
    params = {'message': 'ユーザーの一覧', 'data': data}
    return render(request, 'list.html', params)


@login_required
def create(request,user_id):
    try:
        StripeCustomer.objects.get(user=request.user)
        post_pk = User.objects.get(pk = user_id)

        data = {'message': '', 'form': None}
        if request.method == 'POST':
            form = UserForm(request.POST)
            if form.is_valid():
                instance = form.save(commit=False)
                instance.author = request.user
                instance.save()
                return redirect('mypage', user_id)
            else:
                data['message'] = '再入力して下さい'
                data['form'] = form
        else:
            data['form'] = UserForm()
        return render(request, 'create.html', data)
        
    except StripeCustomer.DoesNotExist:
        return render(request, 'home.html') 


@login_required
def UsersEdit(request,user_id):
    params = {}
    try:
        StripeCustomer.objects.get(user=request.user)
        User.objects.get(pk = user_id)
        if request.method == 'POST':
            form = UserForm(request.POST,instance=data)
            if form.is_valid():
                instance = form.save(commit=False)
                instance.author = request.user
                instance.save()
                return redirect('mypage')
            else:
                data['message'] = '再入力して下さい'
                data['form'] = form
        else:
            params['form'] = UserForm()
        return render(request, 'edit.html', params)
        
    except StripeCustomer.DoesNotExist:
        return render(request, 'home.html')

@login_required
def PostEdit(request, user_id, post_id):
    params = {}
    try:
        StripeCustomer.objects.get(user=request.user)
        User.objects.get(pk = user_id)
        if request.method == 'POST':
            form = UserForm(request.POST,instance=data)
            if form.is_valid():
                instance = form.save(commit=False)
                instance.author = request.user
                instance.save()
                return redirect('/users/'+str(user_id))
            else:
                data['message'] = '再入力して下さい'
                data['form'] = form
        else:
            params['form'] = UserForm(instance=data)
        return render(request, 'edit_post.html', params)
        
    except StripeCustomer.DoesNotExist:
        return render(request, 'home.html')
