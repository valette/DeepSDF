"use strict";
console.clear();

const { desk, qx, THREE, ACVD } = window;

const params = {

    modelDir : "DeepSDFModels/47",
    modelsList : "data/incisors/noms_cluster/cluster 0",
    resolution : 256,
    numberOfVertices : 10000,
    subsamplingThreshold : 100,
    seed : 100,
    size : 200

};

desk.URLParameters.parseParameters( params );
const viewer = new desk.THREE.Viewer();
if ( desk.auto ) viewer.fillScreen();

const animator = new desk.Animator( viewer.render.bind( viewer ) );
animator.getChildren()[ 0 ].setVisibility( "excluded" );
animator.setLoop( false );
viewer.add( animator, { right : 10, bottom : 10 } );

async function reconstruct() {

    const files = await desk.FileSystem.readDirAsync( params.modelsList );
    const names = files.filter( f => f.name.endsWith( ".stl" ) )
        .map( f => f.name.split( "." )[ 0 ] );

    const CSVDir = params.modelDir + "/CSV/";

    const interpolations = [];
    for ( let i = 0; i < names.length; i++ )
        for ( let j = i + 1; j < names.length; j++ )
            interpolations.push( [ names[ i ], names[ j ] ] );

    const rng = new desk.Random( params.seed );
    const results = [];
    const newNames = {};

    for ( let i = 0; i < params.size; i++ ) {

        console.log( "Interpolation " + i );
        const start = window.performance.now();
        const value = Math.floor( rng.random() * interpolations.length );
        const ids = interpolations[ value ];
        const promises = ids.map( v => ACVD.readCSV( CSVDir + v.split( " " ).join( "_" ) + '.csv' ) );
        const csvs = await Promise.all( promises );
        const interpolated = csvs[ 0 ].map( ( v, i ) => v + csvs[ 1 ][ i ] );
        const csv = await desk.FileSystem.writeCachedFileAsync( "interpolated.csv",
            interpolated.join( "," ) );

        const reconstruct = await desk.Actions.executeAsync( {
            experiment : params.modelDir,
            action : "latent2mesh",
            csv,
            resolution : params.resolution
        } );

        const reconstruction = reconstruct.outputDirectory +'/mesh.ply';

        const remesh = await desk.Actions.executeAsync( {
            action : "acvdqp",
            inputMesh : reconstruction,
            numberOfVertices : params.numberOfVertices,
            gradation : 1,
            subsamplingThreshold : params.subsamplingThreshold,
            quadricsLevel : 2
        } );

        const remeshed = remesh.outputDirectory + "simplification.ply";

        const convert = await desk.Actions.executeAsync( {
            action : "mesh2obj",
            inputMesh : remeshed
        } );

        const converted = convert.outputDirectory + "mesh.obj";
        
        const mesh = await viewer.addFileAsync ( converted, { label : "mesh" + i });
        animator.addObject( mesh );
        const stop = window.performance.now();
        const Ids = ids.map( n => parseFloat( n.match(/\d+/g)[ 0 ] ) );
        Ids.sort( ( a, b ) => a - b );
        newNames[ converted ] = Ids.join( "_" ) + ".obj";
        results.push( converted );
        console.log( "Done in  : " + Math.floor( ( stop - start ) / 1000 )  + " seconds");

    }

    await ACVD.downloadArchive( results, { newNames } );

}

reconstruct().catch( console.warn );

