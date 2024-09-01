from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from .ai_logic import get_chatbot_response
from .models import (
Users, UserPolicies, Category, Company, InsurancePolicy, Claim,  Messages, Payment
)
from .serializers import (
 UsersSerializer, UserPoliciesSerializer, CategorySerializer, CompanySerializer, InsurancePolicySerializer, ClaimSerializer,  MessagesSerializer, PaymentSerializer
)


# Create your views here.
class UserLoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        error_message = ""
  
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if Users.objects.filter(user=user).exists():
                user_data = Users.objects.get(user=user)
                user_serializer =  UsersSerializer(user_data)
                return Response(user_serializer.data, status=status.HTTP_200_OK)
            else:
                error_message = 'User data not found'
                return Response({'error': error_message}, status=status.HTTP_404_NOT_FOUND)
        else:
            error_message = 'Invalid login credentials'
            return Response({'error': error_message}, status=status.HTTP_401_UNAUTHORIZED)



@api_view(['POST'])
def chatbot_interact(request):
    if request.method == 'POST':
        user_input = request.data.get('user_input')
        response = get_chatbot_response(user_input)
        return Response(response, status=status.HTTP_200_OK)
    return Response({"error": "Invalid request method"}, status=status.HTTP_401_UNAUTHORIZED)




# @api_view(['GET'])
# def get_simple_subcategories(request):
#     # Filter subcategories that are used in Services
#     used_categories = Category.objects.filter(services__isnull=False).distinct()

#     # Serialize the filtered subcategories
#     category_serializer = CategorySerializer(used_categories, many=True).data
    
#     response = used_categories
#         #save the response in the subcategories.json file 
        
#     with open('categories.json', 'w') as file:
#         json.dump(response.json(), file)
    
#     return Response(category_serializer, status=status.HTTP_200_OK)


# list main categories
@api_view(['GET'])
def categories(request):
    categories = Category.objects.all()
    category_serializer = CategorySerializer(categories, many=True)
    response_data = {'categories': category_serializer.data}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def users_policies(request, userId):
    try:
        user = get_object_or_404(Users, id=userId)
    except NotFound:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        policies = UserPolicies.objects.filter(user=user)  # Adjust for the relationship

        # Categorize policies and count them
        active_policies = []
        on_pause_policies = []
        complete_policies = []

        for policy in policies:
            policy_serializer = UserPoliciesSerializer(policy).data
            if policy.status == 'Active':
                active_policies.append(policy_serializer)
            elif policy.status == 'On Pause':
                on_pause_policies.append(policy_serializer)
            elif policy.status == 'Complete':
                complete_policies.append(policy_serializer)

        # Prepare response data with counts
        response = {
            'total_policies': policies.count(),
            'active': {
                'count': len(active_policies),
                'policies': active_policies
            },
            'on_pause': {
                'count': len(on_pause_policies),
                'policies': on_pause_policies
            },
            'complete': {
                'count': len(complete_policies),
                'policies': complete_policies
            }
        }

        return Response(response, status=status.HTTP_200_OK)

    except ObjectDoesNotExist:
        return Response({"error": "No policies found for this user"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['POST'])
def joinPolicy(request):
    if request.method == 'POST':
        userId = request.data.get('userId')
        policyId = request.data.get('policyId')
       
        user = get_object_or_404(Users, id=userId)
        policy = get_object_or_404(InsurancePolicy, id=policyId)
        
        try:
            # Check if the user is already part of the policy
            join_policy = UserPolicies.objects.get(policy=policy, user=user)
            return Response({'detail': 'User has already joined this policy'}, status=status.HTTP_302_FOUND)
        except UserPolicies.DoesNotExist:
            # If the user is not part of the policy, create the association
            join_policy = UserPolicies.objects.create(policy=policy, user=user)
            join_policy.save()
            return Response({'detail': 'You have now joined this policy'}, status=status.HTTP_201_CREATED)



#display services based on the category and subcategory
@api_view(['POST'])
def displayPolicies(request):
    response_data = {}
    policies = InsurancePolicy.objects.all()

    # Handle filtering based on the POST data
    categoryId = request.data.get('categoryId')
    companyId = request.data.get('companyId')
    policyId = request.data.get('policyId')

    if categoryId:
        policies = policies.filter(company__company_category__id=categoryId)

    if companyId:
        policies = policies.filter(company__id=companyId)

    if policyId:
        policies = policies.filter(id=policyId)

    # Serialize the filtered policies
    insurance_policy_serializer = InsurancePolicySerializer(policies, many=True)
    response_data = {'Policies': insurance_policy_serializer.data}

    return Response(response_data, status=status.HTTP_200_OK)



@api_view(['POST'])
def add_insurance_policy(request):
    if request.method == "POST":
        userId = request.data.get('userId')
        companyId = request.data.get('companyId')
        name = request.data.get('name')
        description = request.data.get('description')
        coverage_amount = request.data.get('coverage_amount')
        premium = request.data.get('premium')
        duration = request.data.get('duration')
        is_active = request.data.get('is_active', True)

        # Ensure boolean conversion for is_active
        if isinstance(is_active, str):
            is_active = is_active.lower() == 'true'

        # Fetch the admin and company instances
        admin = get_object_or_404(Users, id=userId)
        company = get_object_or_404(Company, id=companyId)

        # Check if the admin is allowed to create more policies
        count_policies = InsurancePolicy.objects.filter(company=company).count()
        allow_no_policies = company.allow_policies

        # Validate that the admin is verified and can add more policies
        if admin.verified and count_policies < allow_no_policies:
            try:
                # Create the insurance policy
                policy = InsurancePolicy.objects.create(
                    company=company,
                    name=name,
                    description=description,
                    coverage_amount=coverage_amount,
                    premium=premium,
                    duration=duration,
                    is_active=is_active
                )
                policy.save()
                return Response({'message': 'Insurance policy added successfully'}, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif not admin.verified:
            return Response({'error': 'You are not verified'}, status=status.HTTP_401_UNAUTHORIZED)
        elif count_policies >= allow_no_policies:
            return Response({'error': f'Cannot have more than {allow_no_policies} policies for this company'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error': 'Could not create policy'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['POST'])
def remove_insurance_policy(request):
    if request.method == "POST":
        userId = request.data.get('userId')
        policyId = request.data.get('policyId')  # Insurance policy ID

        # Fetch the admin instance
        admin = get_object_or_404(Users, id=userId)

        # Validate if the admin is verified
        if admin.verified:
            try:
                # Fetch the policy that belongs to the admin and matches the given ID
                policy = InsurancePolicy.objects.get(id=policyId, company__admin=admin)
                policy.delete()
                return Response({'message': 'Insurance policy deleted successfully'}, status=status.HTTP_200_OK)
            except InsurancePolicy.DoesNotExist:
                return Response({'error': 'Policy not found or you are not authorized to delete it'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': f'Failed to remove policy: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'error': 'You are not verified'}, status=status.HTTP_401_UNAUTHORIZED)





@api_view(["GET"])
def get_claims(request, userId):
    user = get_object_or_404(Users, id=userId)
    if user:
        claim = Claim.objects.filter(claimant=user)
        response = ClaimSerializer(claim, many=True).data
        return Response(response, status=status.HTTP_200_OK)
    
    return Response({"error user authentication"},  status=status.HTTP_401_UNAUTHORIZED)


# make insurance claim 
@api_view(['POST'])
def submit_claim(request):
    if request.method == "POST":
        userId = request.data.get('userId')
        policyId = request.data.get('policyId')
        description = request.data.get('description')
        claim_amount = request.data.get('claim_amount')
        title = request.data.get('title')

        # Fetch the user (claimant) and insurance policy instances
        claimant = get_object_or_404(Users, id=userId)
        policy = InsurancePolicy.objects.get(id=policyId)
        # policy = get_object_or_404(InsurancePolicy, id=policyId)

        # Ensure that the claimant is associated with the policy
        if not UserPolicies.objects.filter(user=claimant, policy=policy).exists():
            return Response({'error': 'User is not associated with this policy'}, status=status.HTTP_400_BAD_REQUEST)

        if Claim.objects.filter(claimant=claimant, policy=policy, status='Pending').exists():
            return Response({'error': 'Claim is already pending respone, please wait'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate a unique claim number
        claim_number = get_random_string(length=10).upper()

        try:
            # Create the claim with status set to "Pending"
            claim = Claim.objects.create(
                policy=policy,
                title=title,
                claimant=claimant,
                claim_number=claim_number,
                description=description,
                claim_amount=claim_amount,
                status='Pending'  # Default status for new claims
            )
            claim.save()

            return Response({'message': 'Claim submitted successfully', 'claim_number': claim_number}, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Failed to submit claim: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def update_claim_status(request):
    if request.method == "POST":
        adminId = request.data.get('adminId')
        claim_number = request.data.get('claimNumber')
        claimId = request.data.get('claimId')
        new_status = request.data.get('status')  # Should be 'Approved' or 'Denied'

        # Fetch the admin user and claim instances
        admin = get_object_or_404(Users, id=adminId)
        claim = get_object_or_404(Claim, id=claimId, claim_number=claim_number)

        # Ensure only admins can approve or deny claims
        if admin.verified is False:
            return Response({'error': 'You are not authorized to perform this action'}, status=status.HTTP_403_FORBIDDEN)

        # Validate the new status
        if new_status not in ['Approved', 'Denied']:
            return Response({'error': 'Invalid status. Choose either "Approved" or "Denied".'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update the claim status and set the approval date
            claim.status = new_status
            if new_status == 'Approved':
                claim.approval_date = timezone.now()
            claim.save()

            return Response({'message': f'Claim status updated to {new_status}'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to update claim status: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET', 'POST'])
def getUsersCommunicatedWith(request, receiverId=None):
    try:
        if request.method == 'POST':
            
            sender_Id = request.data.get('senderId')
            receiver_Id = request.data.get('receiverId')
            
            sender = get_object_or_404(Users, id=sender_Id)
            receiver = get_object_or_404(Users, id=receiver_Id)
        
             # Fetch messages where sender=sender and receiver=receiver or sender=receiver and receiver=sender
            messages = Messages.objects.filter(
                Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
            ).order_by('-timestamp').first()
            
            messageSerializer = MessageSerializer(messages).data
            return Response(messageSerializer, status=status.HTTP_200_OK)
  
        receiver = get_object_or_404(Users, id=receiverId)
        
        # Get distinct user IDs from messages where the receiver is either sender or receiver
        user_ids = Messages.objects.filter(
            Q(receiver=receiver) | Q(sender=receiver)
        ).values_list('sender', 'receiver').distinct()

        # Flatten the list and remove the receiver's own ID
        user_ids = set([user_id for pair in user_ids for user_id in pair if user_id != receiver.id])
        
        return Response(list(user_ids), status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'could not get user IDs'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def getChats(request, senderId=None, receiverId=None):
    try:
        sender = get_object_or_404(Users, id=senderId)
        receiver = get_object_or_404(Users, id=receiverId)
        
        # Fetch messages where sender=sender and receiver=receiver or sender=receiver and receiver=sender
        messages = Messages.objects.filter(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
        ).order_by('timestamp')
        
        for message in messages:
            message.readStatus = True
            message.save()
        
        messageSerializer = MessageSerializer(messages, many=True).data
        return Response(messageSerializer, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'could not get messages'}, status=status.HTTP_404_NOT_FOUND)
     

@api_view(['POST'])
def addMessage(request):
    if request.method == 'POST':
        senderId = request.data.get('senderId')
        receiverId = request.data.get('receiverId')
        message = request.data.get('message')
        
        sender = get_object_or_404(Users, id=senderId)
        receiver = get_object_or_404(Users, id=receiverId)
       
        message = Messages.objects.create(sender=sender, receiver=receiver, message=message)
        message.save()
        return Response({'message added'}, status=status.HTTP_201_CREATED)
        
        
@api_view(['POST'])
def deleteMessage(request):
    if request.method == 'POST':
        senderId = request.data.get('senderId')
        receiverId = request.data.get('receiverId')
        messageId = request.data.get('messageId')
        
        sender = get_object_or_404(Users, id=senderId)
        receiver = get_object_or_404(Users, id=receiverId)
    
        try:
            message = Messages.objects.get(id=messageId, sender=sender, receiver=receiver)
            message.delete()
            return Response({'message deleted'}, status=status.HTTP_200_OK)
        except Messages.DoesNotExist():
            return Response({'message has been deleted already'}, status=status.HTTP_204_NO_CONTENT)

        