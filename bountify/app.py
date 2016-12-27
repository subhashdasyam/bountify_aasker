from Bio import Entrez
from collections import defaultdict, Counter
from igraph import *
import time, socket, sys, codecs, csv,string
from flask import Flask, request, render_template, redirect, url_for, Response, stream_with_context, json, jsonify
from flask_socketio import SocketIO, emit

reload(sys)
sys.setdefaultencoding('utf8')

#Flask Config
app = Flask(__name__)
app.config['SECRET_KEY'] = 's3cr37***yt'
app.config['DEBUG'] = True
socketio = SocketIO(app)


#Global Vars
prgs = 0
progress = 0


US_states = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MIN': 'Minneapolis', #special case
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PHI': 'Philadelphia', #special case
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}


#Emit Message Outside
def _e(message):
    socketio.emit('my response', {'data':message })

@socketio.on('connect')
def chat_connect():
    print ('connected')

@socketio.on('disconnect')
def chat_disconnect():
    print ("Client disconnected")

@socketio.on('broadcast')
def chat_broadcast(message):
    print ("test")
    emit("my response", {'data': message})

def find_between_r( s, first, last ):
    try:
        start = s.rindex( first ) + len( first ) + 1
        end = s.rindex( last, start )
        return s[start:end]
    except ValueError:
        return 'Not found'

def clean_country(c):
    try:
        pos = c.rindex('(')
        return c[0:pos-1]
    except ValueError:
        return c

def search_and_fetch_fields(area,country):
    _e('Searching Key Opinion leaders for disease {0} from country {1}, please wait'.format(area,country))
    Entrez.email = 'subhashdasyam@bountify.com'
    search_handle = Entrez.esearch(db='pubmed',sort='relevance',retmax=100000,retmode='xml',term=area)    
    search_results = Entrez.read(search_handle)
    _e('Search completed for area {0}'.format(area))
    if 'IdList' in search_results:
        ids = ','.join(search_results['IdList'])
        _e('Fetching Key Opinion leaders for disease {0} from {1}, please wait '.format(area,country))
        fetch_handle = Entrez.efetch(db='pubmed',retmode='xml',id=ids)
        fetch_results = Entrez.read(fetch_handle)
        _e('Fetch completed for disease {0}, proceeding for next steps, please wait'.format(area))
        return fetch_results
    else:
        return False


author2affiliation = dict()


@app.route('/')
def main():
    _e('main page')
    return render_template('index.html')

@app.route('/search',methods = ['POST'])
def search():
    global prgs
    global progress
    if request.method == 'POST':
        area = request.form.get('therapeutic_area', 'brain injury')
        area_name = area.replace (" ", "_")
        the_country = request.form.get('country', 'USA')
        top_kols = float(request.form.get('topkols', '10'))
        start_time = time.time()
        saff = search_and_fetch_fields('\"'+area+'\"',the_country)
        nodes = set()
        edges = defaultdict(list)
        country = dict()        
        _e('Starting process, please wait')
        prgs = [len(x) for i,x in saff.iteritems()]
        prgs = prgs[0]
        for i, x in saff.iteritems():
            for paper in x:                
                _e('Processing '+str(progress)+'/'+str(prgs))
                #print 'Processing '+str(progress)+'/'+str(prgs)
                if 'MedlineCitation' in paper.keys() and 'Article' in paper['MedlineCitation'].keys() and 'AuthorList' in paper['MedlineCitation']['Article'].keys():
                    author_list = paper['MedlineCitation']['Article']['AuthorList']
                    authors = []
                    for index in range(0, min(len(author_list),12)):
                        a = author_list[index]
                        name = ''
                        if 'LastName' in a.keys() and 'ForeName' in a.keys():
                            name = a['ForeName'].replace(' ','_')+'_'+a['LastName'].replace(' ','')
                            authors.append(name)
                        if name not in country.keys() or country[name] == 'Not found':
                            if 'AffiliationInfo' in a.keys():
                                if len(a['AffiliationInfo']) > 0:
                                    if 'Affiliation' in a['AffiliationInfo'][0].keys():
                                        s_country = find_between_r(a['AffiliationInfo'][0]['Affiliation'], ',', '.')
                                        if 'China' in s_country:
                                            s_country = 'China'
                                        if 'United States' in s_country:
                                            s_country = 'USA'
                                        if s_country in US_states.keys() or s_country in US_states.values():
                                            s_country = 'USA'

                                        country[name] = s_country
                                        author2affiliation[name] = a['AffiliationInfo'][0]['Affiliation'].replace("\"", "")
                                else:
                                    country[name] = 'Not found'

                    # create edges
                    for i in range(len(authors)):
                        u = authors[i]
                        nodes.add(u)
                        for j in range(i+1,len(authors)):
                            v = authors[j]
                            nodes.add(v)
                            edges[u].append(v)
                            edges[v].append(u)
                #time.sleep(0.1)
                progress += 1
        f = codecs.open('results/co-author_network_'+area_name+'_'+the_country+'.pairs', 'w', 'utf-8')
        for k in edges.keys():
            neighbors = Counter(edges[k])
            for n in neighbors.keys():
                if n > k:
                    f.write(str(k)+' '+str(n)+' '+str(neighbors[n])+'\n')
        f.close()
        ##
        ## read network
        ##
        # extract largest connected component
        
        G = Graph.Read_Ncol('results/co-author_network_'+area_name+'_'+the_country+'.pairs', directed=False)
        components = G.components(WEAK)
        G = components.giant()
        vs = VertexSeq(G)
        n_kols = int(round(top_kols * G.vcount() / 100.0))

        # calculate centrality measures
        degrees = dict(zip(vs['name'],G.degree()))
        closeness = dict(zip(vs['name'],G.closeness()))
        eigenvector_centrality = dict(zip(vs['name'],G.eigenvector_centrality()))
        betweenness = dict(zip(vs['name'],G.betweenness()))

        # get top KOLs
        top_degree = sorted(degrees.items(),key=operator.itemgetter(1),reverse=True)
        top_closeness = sorted(closeness.items(),key=operator.itemgetter(1),reverse=True)
        top_eigenvector = sorted(eigenvector_centrality.items(),key=operator.itemgetter(1),reverse=True)
        top_betweenness = sorted(betweenness.items(),key=operator.itemgetter(1),reverse=True)

        # get kols
        global_kols = set()
        local_kols = []
        for i in range(G.vcount()):
            d = top_degree[i][0]
            c = top_closeness[i][0]
            e = top_eigenvector[i][0]
            b = top_betweenness[i][0]
            if i <= n_kols:
                global_kols.add(d)
                global_kols.add(c)
                global_kols.add(e)
                global_kols.add(b)
            if clean_country(country[d]).lower() == the_country.lower() and d not in local_kols:
                local_kols.append(d)
            if clean_country(country[c]).lower() == the_country.lower() and c not in local_kols:
                local_kols.append(c)
            if clean_country(country[e]).lower() == the_country.lower() and e not in local_kols:
                local_kols.append(e)
            if clean_country(country[b]).lower() == the_country.lower() and b not in local_kols:
                local_kols.append(b)

        # write to csv file
        #Global %
        with open('results/kolresults_'+area_name+'_'+the_country+'_global.html', 'w') as f:
            #f.write('FirstName\tMiddleName\tLastName\tAffiliation\n')
            f.write('<table class="table table-striped"><thead><th>FirstName</th><th>MiddleName</th><th>LastName</th><th>Affiliation</th></thead><tbody>')
            for k in global_kols:
                c = clean_country(country[k])

                if c.lower() == the_country.lower():
                    full_name = k.split('_')
                    aff = "\""+author2affiliation[k]+"\""
                    f.write('<tr>')
                    if len(full_name) == 3:
                        #f.write(full_name[0]+'\t'+full_name[1]+'\t'+full_name[2]+'\t'+aff+'\n')
                        f.write('<td>'+full_name[0]+'</td><td>'+full_name[1]+'</td><td>'+full_name[2]+'</td><td>'+aff+'</td>')
                    else:
                        #f.write(full_name[0]+'\t \t'+full_name[1]+'\t'+aff+'\n')
                        f.write('<td>'+full_name[0]+'</td><td></td><td>'+full_name[1]+'</td><td>'+aff+'</td>')
                    f.write('</tr>')
            f.write('</tbody></table>')
            f.close()

        # Local % (country-specific)
        with open('results/kolresults_'+area_name+'_'+the_country+'_local.html', 'w') as f:
            #f.write('FirstName\tMiddleName\tLastName\tAffiliation\n')
            f.write('<table class="table table-striped"><thead><th>FirstName</th><th>MiddleName</th><th>LastName</th><th>Affiliation</th></thead><tbody>')
            local_n_kols = int(round(top_kols * len(local_kols) / 100.0))
            for k in local_kols[:min(local_n_kols,len(local_kols))]:
                full_name = k.split('_')
                aff = "\""+author2affiliation[k]+"\""
                f.write('<tr>')
                if len(full_name) == 3:
                    #f.write(full_name[0]+'\t'+full_name[1]+'\t'+full_name[2]+'\t'+aff+'\n')
                    f.write('<td>'+full_name[0]+'</td><td>'+full_name[1]+'</td><td>'+full_name[2]+'</td><td>'+aff+'</td>')
                else:
                    #f.write(full_name[0]+'\t \t'+full_name[1]+'\t'+aff+'\n')
                    f.write('<td>'+full_name[0]+'</td><td></td><td>'+full_name[1]+'</td><td>'+aff+'</td>')
                f.write('</tr>')
            f.write('</tbody></table>')
            f.close()


        # with open('results/kolresults_'+area_name+'_'+the_country+'_global.html', 'w') as f:
        #     f.write('<table class="table table-striped">')
        #     f.write('<thead><th>FirstName</th><th>MiddleName</th><th>LastName</th><th>Affiliation</th></thead><tbody>')
        #     #f.write('FirstName\tMiddleName\tLastName\tAffiliation\n')
        #     for k in global_kols:
        #         c = clean_country(country[k])

        #         if c.lower() == the_country.lower():
        #             full_name = k.split('_')
        #             aff = "\""+author2affiliation[k]+"\""
        #             f.write('<tr>')
        #             if len(full_name) == 3:
        #                 #f.write(full_name[0]+'\t'+full_name[1]+'\t'+full_name[2]+'\t'+aff+'\n')
        #                 f.write('<td>'+full_name[0]+'</td><td>'+full_name[1]+'</td><td>'+full_name[2]+'</td><td>'+aff+'</td>')
        #             else:
        #                 #f.write(full_name[0]+'\t \t'+full_name[1]+'\t'+aff+'\n')
        #                 f.write('<td>'+full_name[0]+'</td><td>&nbsp;&nbsp;&nbsp;</td><td>'+full_name[2]+'</td><td>'+aff+'</td>')
        #             f.write('</tr>')
        #     f.write('</tbody></table>')
        #     f.close()

        # Local % (country-specific)
        # with open('results/kolresults_'+area_name+'_'+the_country+'_local.html', 'w') as f:
        #     f.write('<table class="table table-striped">')
        #     f.write('<thead><th>FirstName</th><th>MiddleName</th><th>LastName</th><th>Affiliation</th></thead><tbody>')
        #     local_n_kols = int(round(top_kols * len(local_kols) / 100.0))
        #     for k in local_kols[:min(local_n_kols,len(local_kols))]:
        #         full_name = k.split('_')
        #         aff = "\""+author2affiliation[k]+"\""
        #         f.write('<tr>')
        #         if len(full_name) == 3:
        #             f.write('<td>'+full_name[0]+'</td><td>'+full_name[1]+'</td><td>'+full_name[2]+'</td><td>'+aff+'</td>')
        #         else:
        #             f.write('<td>'+full_name[0]+'</td><td>&nbsp;&nbsp;&nbsp;</td><td>'+full_name[2]+'</td><td>'+aff+'</td>')
        #         f.write('</tr>')
        #     f.write('</tbody></table>')
        #     f.close()
        _e('Completed')
        with open('results/kolresults_'+area_name+'_'+the_country+'_global.html', 'r') as g_file:
            global_content = g_file.read()
        with open('results/kolresults_'+area_name+'_'+the_country+'_local.html', 'r') as l_file:
            local_content = l_file.read()
        _e({"g":global_content,"l":local_content})
        #print 'It took', time.time()-start_time, 'seconds.'
    return 'Success'
if __name__ == '__main__':
    socketio.run(app)
    #app.run(host='0.0.0.0', port=8080)
    #socketio.run(app, host='0.0.0.0',port=8080)

